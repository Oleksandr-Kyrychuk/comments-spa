import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'comments_project.settings')

app = Celery('comments_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()