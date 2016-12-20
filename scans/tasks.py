from __future__ import absolute_import, unicode_literals
from django.conf import settings
from celery import shared_task, Celery, Task, chord
from .models import *
from webscanner.logger import logger
from webscanner.settings import *
from webscanner.plugin_api import *
from scans.Zipper import *
from plugins import *


import subprocess, os, datetime, sys, glob, importlib, inspect, re

@shared_task
def delegate(plugin_name, model_id):
    """
    module_name is the name of the plugin's interfacing class and
                 its interfacing class must be of type AbstractPlugin
    model_id     is pased in for later lookup inside the plugin interface's instance
    """
    #plugin   = find_interface(plugin_name)
    plugin   = find_class(plugin_name)
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


def find_all_interfaces():
    all_interfaces    = list()
    plugin_interfaces = glob.glob(os.path.join(os.path.basename(PLUGINS_DIR),"*.py"))
    for item in plugin_interfaces:
        module_name     = item.replace("/", ".").replace(".py", "")
        importlib.import_module(module_name)
        classes         = [class_name[1] for class_name in inspect.getmembers(sys.modules[module_name], inspect.isclass)]
        for class_name in classes:
            plugin_name = getattr(class_name, "PLUGIN_NAME", None)
            if plugin_name and issubclass(class_name, AbstractPlugin):
                all_interfaces.append((class_name, plugin_name))
    return all_interfaces

        
def find_interface(plugin_name):
    class_objects = [classes[0] for classes in find_all_interfaces() if classes[1] == plugin_name]
    if len(class_objects) > 0:
        return class_objects[0]
    else:
        return None

def find_class(import_path):
    if '<class' in import_path:
        import_path = re.findall("'([^']*)'", import_path)[0]
    components = import_path.split('.')
    module     = importlib.import_module('.'.join(components[:-1]))
    return getattr(module, components[-1], None)
