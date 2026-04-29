import os
from celery import Celery

# Initialize Celery and tell it EXACTLY where to find the tasks
celery_instance = Celery(
    'async_tasks',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    include=['async_tasks.tasks']  # <--- THIS IS THE FIX
)

celery_instance.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)