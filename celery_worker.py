# celery_worker.py

import os
from celery import Celery
from celery_app import celery_app
from tasks.price_check_task  import check_price

celery_app = Celery(
    "worker",
    broker="redis://3.145.175.131:6379/0",
    backend="redis://3.145.175.131:6379/0"
)

celery_app.autodiscover_tasks(['tasks'])