from celery import Celery
from app.config import settings


def _make_redis_url(url: str) -> str:
    if url and url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}ssl_cert_reqs=CERT_NONE"
    return url or "memory://"


_redis_url = _make_redis_url(settings.REDIS_URL)
_result_backend = _make_redis_url(settings.CELERY_RESULT_BACKEND)

celery_app = Celery(
    "xenoguard",
    broker=_redis_url,
    backend=_result_backend,
    include=["app.workers.tasks"],
)

_ssl_opts = {"ssl_cert_reqs": "CERT_NONE"}

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
    broker_use_ssl=_ssl_opts if "rediss://" in _redis_url else None,
    redis_backend_use_ssl=_ssl_opts if "rediss://" in _result_backend else None,
)
