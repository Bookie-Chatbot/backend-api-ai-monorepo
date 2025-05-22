# celery_worker.py

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://3.145.175.131:6379/0",
    backend="redis://3.145.175.131:6379/0"
)

celery_app.autodiscover_tasks()