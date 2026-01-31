import asyncio
import logging
import signal
import time
import traceback as tb
from collections import defaultdict
from importlib import import_module

from asgiref.sync import sync_to_async
from django.db import close_old_connections

from django_vtasks.backends.base import BaseTaskBackend

from .conf import settings
from .metrics import ACTIVE_TASKS, QUEUE_DEPTH, TASK_DURATION, TASKS_PROCESSED
from .signals import task_failure, task_finished, task_started

logger = logging.getLogger(__name__)


def _run_sync_with_db_cleanup(func, args, kwargs):
    """
    Run a sync function with Django database connection cleanup.

    This ensures stale database connections are closed before and after
    task execution, preventing "connection is closed" errors when using
    connection poolers like PgBouncer or Django's psycopg3 pool.
    """
    close_old_connections()
    try:
        return func(*args, **kwargs)
    finally:
        close_old_connections()


# Async version runs cleanup in the same thread Django uses for sync_to_async
_async_close_old_connections = sync_to_async(close_old_connections, thread_sensitive=True)


class Worker:
    def __init__(
        self,
        backend: "BaseTaskBackend",
        queues: list[str] | None = None,
        concurrency: int | None = None,
        batch_config: dict[str, dict] | None = None,
        health_check_file: str | None = None,
    ) -> None:
        self.backend = backend
        self.queues = queues or settings.VTASKS_QUEUES
        self.concurrency = concurrency or settings.VTASKS_CONCURRENCY
        self.batch_config = batch_config or settings.VTASKS_BATCH_QUEUES
        self.health_check_file = health_check_file
        self.running = False
        self.sem: asyncio.Semaphore | None = None

    async def run(self, handle_signals: bool = True, run_once: bool = False) -> None:
        try:
            import uvloop

            uvloop.install()
            logger.info("uvloop installed.")
        except ImportError:
            logger.info("uvloop not found, using default asyncio event loop.")

        if self.running:
            return

        self.sem = asyncio.Semaphore(self.concurrency)
        self.running = True

        if self.health_check_file:
            self.start_heartbeat(self.health_check_file)

        loop = asyncio.get_running_loop()

        logger.info(
            "Starting worker with concurrency=%d, queues=%s, backend=%s",
            self.concurrency,
            self.queues,
            self.backend.__class__.__name__,
        )

        if handle_signals:

            def _stop_signal_handler() -> None:
                asyncio.create_task(self.stop())

            loop.add_signal_handler(signal.SIGINT, _stop_signal_handler)
            loop.add_signal_handler(signal.SIGTERM, _stop_signal_handler)

        await self.backend._rescue_tasks()

        try:
            consumers = []
            for queue in self.queues:
                consumers.append(asyncio.create_task(self.consume_queue(queue, run_once)))

            await asyncio.gather(*consumers)
        finally:
            logger.info("Waiting for active tasks to finish...")
            if self.sem:
                for _ in range(self.concurrency):
                    await self.sem.acquire()
                for _ in range(self.concurrency):
                    self.sem.release()
            self.running = False
            logger.info("Worker stopped.")

    async def consume_queue(self, queue: str, run_once: bool = False) -> None:
        batch_options = self.batch_config.get(queue)
        sleep_time = 0.1
        last_metric_update = 0.0

        while self.running:
            try:
                # Update queue depth metric every 15 seconds
                now = time.monotonic()
                if now - last_metric_update > 15:
                    try:
                        depth = await self.backend.get_queue_depth(queue)
                        QUEUE_DEPTH.labels(queue=queue).set(depth)
                        last_metric_update = now
                    except Exception:
                        logger.warning("Failed to update queue depth metric for %s", queue)

                found_work = False
                if batch_options:
                    tasks = await self.backend.fetch_batch(
                        queue, batch_options["count"], batch_options["timeout"]
                    )
                    if tasks:
                        if self.sem:
                            await self.sem.acquire()
                        asyncio.create_task(self.process_batch(tasks, queue))
                        found_work = True
                else:
                    task = await self.backend._fetch_task([queue])
                    if task:
                        if self.sem:
                            await self.sem.acquire()
                        asyncio.create_task(self.process_task(task))
                        found_work = True

                if run_once:
                    break

                if found_work:
                    sleep_time = 0.1
                else:
                    await asyncio.sleep(sleep_time)
                    sleep_time = min(sleep_time * 2, 1)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.error("Consumer error for queue %s", queue, exc_info=True)
                await asyncio.sleep(1)

    def start_heartbeat(self, path: str) -> None:
        """Start a background task to update a health check file."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(path))

    async def _heartbeat_loop(self, path: str) -> None:
        """Update the mtime of the health check file every 5 seconds."""
        logger.info("Starting heartbeat at %s", path)

        def _write_heartbeat():
            with open(path, "w") as f:
                f.write(str(time.time()))

        try:
            while self.running:
                try:
                    await asyncio.to_thread(_write_heartbeat)
                except Exception:
                    logger.warning("Failed to update heartbeat file: %s", path)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        if not self.running:
            return

        logger.info("Shutting down worker...")
        self.running = False

        if hasattr(self, "_heartbeat_task"):
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def process_batch(self, tasks: list[dict], queue: str) -> None:
        """
        Process a batch of tasks from a batch queue.

        Tasks are grouped by their function type and each group is processed separately.
        This allows a single batch queue to handle multiple task types efficiently.
        """
        ACTIVE_TASKS.labels(queue=queue).inc()
        start_time = time.monotonic()
        task_ids = [task.get("id", "unknown") for task in tasks]
        logger.info(
            "Processing batch of %d tasks from queue %s: %s",
            len(tasks),
            queue,
            task_ids,
        )

        try:
            if not tasks:
                logger.warning("No tasks to process in batch for queue %s", queue)
                return

            # Group tasks by their function
            tasks_by_func = defaultdict(list)
            for task in tasks:
                func_path = task.get("func")
                if not func_path:
                    logger.error("Task %s has no 'func' field, skipping", task.get("id"))
                    await self.backend._fail_task(task, ValueError("Task has no 'func' field"))
                    continue
                tasks_by_func[func_path].append(task)

            # Process each group of tasks separately
            for func_path, func_tasks in tasks_by_func.items():
                logger.info(
                    "Processing %d tasks of type %s in batch queue %s",
                    len(func_tasks),
                    func_path,
                    queue,
                )
                group_start = time.monotonic()
                try:
                    module_path, func_name = func_path.rsplit(".", 1)
                    module = import_module(module_path)
                    func = getattr(module, func_name).func

                    if asyncio.iscoroutinefunction(func):
                        await _async_close_old_connections()
                        try:
                            await func(func_tasks)
                        finally:
                            await _async_close_old_connections()
                    else:
                        await asyncio.to_thread(_run_sync_with_db_cleanup, func, (func_tasks,), {})

                    await self.backend._ack_batch(func_tasks)

                    group_duration = time.monotonic() - group_start
                    TASK_DURATION.labels(task_name=func_path, queue=queue).observe(group_duration)
                    TASKS_PROCESSED.labels(task_name=func_path, queue=queue, status="success").inc(
                        len(func_tasks)
                    )

                    logger.info(
                        "Successfully processed batch of %d tasks for %s",
                        len(func_tasks),
                        func_path,
                    )
                except Exception as e:
                    group_duration = time.monotonic() - group_start
                    TASK_DURATION.labels(task_name=func_path, queue=queue).observe(group_duration)
                    TASKS_PROCESSED.labels(task_name=func_path, queue=queue, status="failure").inc(
                        len(func_tasks)
                    )

                    logger.error(
                        "Failed to process batch for function %s in queue %s",
                        func_path,
                        queue,
                        exc_info=True,
                    )
                    for task in func_tasks:
                        await self.backend._fail_task(task, e)

            duration = time.monotonic() - start_time
            logger.info("Finished processing batch of %d tasks in %.4fs", len(tasks), duration)
        except Exception as e:
            logger.error("Failed to process batch for queue %s", queue, exc_info=True)
            for task in tasks:
                await self.backend._fail_task(task, e)
        finally:
            ACTIVE_TASKS.labels(queue=queue).dec()
            if self.sem:
                self.sem.release()

    async def process_task(self, task_data: dict) -> None:
        start_time = time.monotonic()
        task_id = task_data.get("id", "unknown")
        func_path = task_data.get("func", "unknown")
        queue = task_data.get("queue", "unknown")
        ACTIVE_TASKS.labels(queue=queue).inc()
        logger.info("Processing task %s: %s", task_id, func_path)
        try:
            try:
                task_started.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    args=task_data.get("args"),
                    kwargs=task_data.get("kwargs"),
                )
            except Exception:
                logger.exception("Error sending task_started signal")

            module_path, func_name = task_data["func"].rsplit(".", 1)
            module = import_module(module_path)
            func = getattr(module, func_name).func

            # Filter out internal kwargs
            filtered_kwargs = {
                k: v
                for k, v in task_data["kwargs"].items()
                if k
                not in [
                    "queue_name",
                    "unique",
                    "unique_key",
                    "ttl",
                    "remove_unique_on_complete",
                ]
            }

            if asyncio.iscoroutinefunction(func):
                await _async_close_old_connections()
                try:
                    await func(*task_data["args"], **filtered_kwargs)
                finally:
                    await _async_close_old_connections()
            else:
                await asyncio.to_thread(
                    _run_sync_with_db_cleanup,
                    func,
                    task_data["args"],
                    filtered_kwargs,
                )

            await self.backend._ack_task(task_data)
            duration = time.monotonic() - start_time

            TASK_DURATION.labels(task_name=func_path, queue=queue).observe(duration)
            TASKS_PROCESSED.labels(task_name=func_path, queue=queue, status="success").inc()

            logger.info("Task %s finished in %.4fs", task_id, duration)

            try:
                task_finished.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    duration=duration,
                )
            except Exception:
                logger.exception("Error sending task_finished signal")
        except Exception as e:
            duration = time.monotonic() - start_time
            TASK_DURATION.labels(task_name=func_path, queue=queue).observe(duration)
            TASKS_PROCESSED.labels(task_name=func_path, queue=queue, status="failure").inc()

            logger.error("Task %s failed", task_id, exc_info=True)
            await self.backend._fail_task(task_data, e)

            try:
                task_failure.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    exception=e,
                    traceback=tb.format_exc(),
                )
            except Exception:
                logger.exception("Error sending task_failure signal")
        finally:
            ACTIVE_TASKS.labels(queue=queue).dec()
            if self.sem:
                self.sem.release()
