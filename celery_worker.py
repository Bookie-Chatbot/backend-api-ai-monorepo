# celery_worker.py

import os
from celery import Celery

# 경로 문제 방지용 (선택)
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

celery_app = Celery(
    "worker",
    broker="redis://3.145.175.131:6379/0",
    backend="redis://3.145.175.131:6379/0"
)

celery_app.autodiscover_tasks(['tasks'])