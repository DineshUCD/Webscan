import plugin_api
from celery import Celery

celery = Celery('tasks', backend='redis://localhost', broker='pqamqp://')

@celery.task
def run_plugin(target, plan, scan_id):
    plugin = getattr(plugin_api, target)
    


