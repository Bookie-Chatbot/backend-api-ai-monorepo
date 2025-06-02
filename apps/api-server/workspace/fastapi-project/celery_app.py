# celery_app.py
from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://3.145.175.131:6379/0",
    backend="redis://3.145.175.131:6379/0"
)

celery_app.conf.timezone = "Asia/Seoul"
celery_app.conf.task_routes = {
    "tasks.price_check_task.check_price": {"queue": "check_price"},
}

celery_app.autodiscover_tasks(['tasks'])
