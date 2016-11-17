from __future__ import absolute_import, unicode_literals
from django.conf import settings
from celery import shared_task, Celery, Task
from .models import *
from webscanner.logger import logger

import webscanner.plugin_api
import subprocess, os, datetime

@shared_task
def delegate(plugin_class, scan_id):
    plugin = getattr(webscanner.plugin_api, plugin_class)


class ScanPlan(object):
    """
    Scan selections launch plugins that spawn external tools. 
    This plugin can wait until all processes finish, capture the date,
    process it immediately and report the results back.
    """
    def __init__(self, scan_id, *args, **kwargs):

        self.scan_id = scan_id
        pass        
