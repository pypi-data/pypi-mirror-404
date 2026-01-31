import asyncio
import fcntl
import logging
import os
import tempfile

from django.tasks import task_backends

from .conf import settings
from .scheduler import Scheduler
from .worker import Worker


def get_worker_application(django_app):
    worker_instance = None
    scheduler_instance = None
    lock_file = None
    lock_fd = None

    async def asgi(scope, receive, send):
        nonlocal worker_instance, scheduler_instance, lock_file, lock_fd

        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    try:
                        # Instantiate worker
                        backend = task_backends["default"]

                        worker_instance = Worker(
                            backend=backend,
                            concurrency=settings.VTASKS_CONCURRENCY,
                            queues=settings.VTASKS_QUEUES,
                            batch_config=settings.VTASKS_BATCH_QUEUES,
                        )

                        # Run worker in the background
                        asyncio.create_task(worker_instance.run(handle_signals=False))

                        # Instantiate and run scheduler if enabled
                        if settings.VTASKS_RUN_SCHEDULER and settings.VTASKS_SCHEDULE:
                            # Try to acquire a local lock to ensure only one scheduler per container
                            lock_file = os.path.join(tempfile.gettempdir(), "django_vtasks_scheduler.lock")
                            try:
                                lock_fd = open(lock_file, "w")
                                fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                                # Lock acquired, start scheduler
                                scheduler_instance = Scheduler(
                                    backend=backend, schedule=settings.VTASKS_SCHEDULE
                                )
                                asyncio.create_task(scheduler_instance.run())
                                logging.info("Local scheduler lock acquired, starting scheduler.")
                            except OSError:
                                logging.info(
                                    "Could not acquire local scheduler lock, skipping scheduler start."
                                )
                                if lock_fd:
                                    lock_fd.close()
                                    lock_fd = None

                        await send({"type": "lifespan.startup.complete"})
                    except Exception as e:
                        logging.error("Worker/Scheduler startup failed: %s", e, exc_info=True)
                        await send({"type": "lifespan.startup.failed", "message": str(e)})

                elif message["type"] == "lifespan.shutdown":
                    try:
                        if worker_instance:
                            await worker_instance.stop()
                        if scheduler_instance:
                            await scheduler_instance.stop()

                        if lock_fd:
                            try:
                                fcntl.lockf(lock_fd, fcntl.LOCK_UN)
                                lock_fd.close()
                            except Exception:
                                pass

                        await send({"type": "lifespan.shutdown.complete"})
                    except Exception as e:
                        logging.error("Worker/Scheduler shutdown failed: %s", e, exc_info=True)
                        await send({"type": "lifespan.shutdown.failed", "message": str(e)})
                    return
        else:
            await django_app(scope, receive, send)

    return asgi
