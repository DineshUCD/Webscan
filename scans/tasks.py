from __future__ import absolute_import, unicode_literals
from django.conf import settings
from celery import shared_task, Celery, Task, chord
from .models import *
from webscanner.logger import logger
from webscanner.settings import *
from webscanner.plugin_api import *
from scans.Zipper import *
from plugins.w3af import *

import plugins

import subprocess, os, datetime, sys, glob, importlib

@shared_task
def delegate(plugin_name, model_id):
    """
    module_name is the name of the plugin's interfacing class and
                 its interfacing class must be of type AbstractPlugin
    model_id     is pased in for later lookup inside the plugin interface's instance
    """
    plugin   = find_interface(plugin_name)
    instance = plugin(model_pk=int(model_id))
    return instance.do_start()

@shared_task
def collect_results(meta_collection):
    """
    This callback can only be executed after all the tasks in the chord header have returned.
    meta_collection is a list of lists which contains files for each scanner in the plan.
    plan_instance handles the coordination of plugins in the Django view.
    """
    meta_files = list()
    for scan_files in meta_collection:
        meta_files.extend(scan_files)
    print meta_files
    return meta_files

def find_interface(plugin_name):
    try:
        plugin_interfaces = glob.glob( os.path.join( os.path.basename(PLUGINS_DIR), "*.py") )
        for item in plugin_interfaces:
            module_name = item.replace("/", ".").replace(".py", "")
            noninstance = getattr(importlib.import_module(module_name), plugin_name, None)
            if noninstance:
                return noninstance
    except (AttributeError, ImportError) as plugin_finder_error:
        logger.critical(plugin_finder_error.message)
        sys.exit(1)
    else:
        return None
