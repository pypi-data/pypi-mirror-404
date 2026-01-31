# django-vtasks

**Valkey Tasks. Very Fast Tasks.**

From the team at [GlitchTip](https://glitchtip.com), `django-vtasks` is a lightweight, async-first task queue for Django 6.0+.

**Status**: Newly feature complete. Beta quality. Use and report bugs.

## Why django-vtasks?

- **Async-first** - Native `asyncio` worker for high-performance I/O
- **Flexible backends** - Start with Postgres, scale to Valkey without rewriting code
- **Lightweight** - Minimal dependencies, modern codebase
- **Embedded mode** - Run tasks in your ASGI server or as standalone workers

## Features

- Dual backends: Database (Postgres/SQLite/MySQL) and Valkey (Redis-compatible)
- Scheduled tasks with cron syntax
- Unique tasks (Mutex and Throttle patterns)
- Batch processing for high-throughput queues
- Prometheus metrics
- Django admin interface for task management

![Admin Interface](/docs/admin.png)

## Requirements

- Python 3.12+
- Django 6.0+
- Valkey 7+ (or Redis 7+) for Valkey backend

## Quick Start

```bash
pip install django-vtasks
```

```python
# settings.py
INSTALLED_APPS = ["django_vtasks", "django_vtasks.db"]

TASKS = {
    "default": {
        "BACKEND": "django_vtasks.backends.db.DatabaseTaskBackend",
    }
}
```

```python
# myapp/tasks.py
from django_vtasks import task

@task
def send_email(user_id):
    # Your task logic
    pass
```

```python
# In your views
send_email.enqueue(user_id)
# or async
await send_email.aenqueue(user_id)
```

```bash
# Run the worker
python manage.py runworker
```

## Documentation

Full documentation is available at **[django-vtasks.glitchtip.com](https://django-vtasks.glitchtip.com)**

- [Getting Started](https://django-vtasks.glitchtip.com/getting-started/)
- [Guide](https://django-vtasks.glitchtip.com/guide/) - Unique tasks, batching, scheduling, and more
- [Configuration](https://django-vtasks.glitchtip.com/configuration/) - All settings reference
- [Deployment](https://django-vtasks.glitchtip.com/deployment/) - Standalone workers, embedded mode, Kubernetes

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

*Built by the [GlitchTip](https://glitchtip.com) team.*
