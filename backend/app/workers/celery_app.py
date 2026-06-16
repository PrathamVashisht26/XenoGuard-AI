from celery import Celery
from app.config import settings

_redis_url = settings.REDIS_URL if settings.REDIS_URL else "memory://"
_result_backend = settings.CELERY_RESULT_BACKEND if settings.CELERY_RESULT_BACKEND else "cache+memory://"

celery_app = Celery(
    "xenoguard",
    broker=_redis_url,
    backend=_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_always_eager=(_redis_url == "memory://"),
    task_eager_propagates=True,
)
