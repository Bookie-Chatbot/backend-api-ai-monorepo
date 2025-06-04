# celery_worker.py

import os
from celery import Celery
from .celery_app import celery_app
from apps.api_server.workspace.fastapi_project.tasks import price_check_task
