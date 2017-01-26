from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, Task, chord
from celery.utils import uuid

# set the defauly Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webscanner.settings')

app = Celery('webscanner')

# Using a string here means the worker does not have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means that all celery-related configuration keys
#                      should have a 'CELERY_' prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

