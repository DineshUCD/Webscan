from __future__ import absolute_import, unicode_literals
from django.conf import settings
from celery import shared_task, Celery, Task, chord
from .models import *
from webscanner.logger import logger
from webscanner.settings import *
from webscanner.plugin_api import *
from plugins import *

import plugins

import subprocess, os, datetime, sys, glob, importlib

@shared_task
def delegate(plugin_class, model_id):
    if not plugin_class and not isinstance(plugin_class, AbstractPlugin):
        return None

    instance = plugin_class(model_pk=model_id`)
    return instance.do_run()

class ScanPlan(object):
    """
    Scan selections launch plugins that spawn external tools. 
    This plugin can wait until all processes finish, capture the date,
    process it immediately and report the results back.
    """
    def __init__(self, plugin_classes, scan_id, *args, **kwargs):
        """
        Obtains the classes for respective plugins and instantiates variables
        to pre-/post-process series of scans.
        """
        self.plugins = list()
        try:
            self.scan         = Scan.objects.get(pk=int(scan_id))
            plugin_interfaces = glob.glob( os.path.join( os.path.basename(PLUGINS_DIR), "*.py") )

            for plugin_name in plugin_classes:
                for item in plugin_interfaces:
                   
                    module_name = item.replace("/", ".").replace(".py", "")
                    print module_name
                    noninstance = getattr(importlib.import_module(module_name), plugin_name, None)
                    if noninstance:
                        self.plugins.append(noninstance)

        except (AttributeError, ImportError, Scan.DoesNotExist) as plugin_handler_error:
            logger.critical(plugin_handler_error.message)
            sys.exit(1)
        else:
            self.zipper = ZipArchive(scan=int(scan_id))

