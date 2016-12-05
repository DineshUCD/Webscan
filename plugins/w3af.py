import logging, os, sys, subprocess, configparser

from django.conf import settings
from webscanner.plugin_api import *
from scans.models import *

class W3af(AbstractPlugin):
    PLUGIN_NAME = "W3af"
    PLUGIN_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        super(W3af, self).__init__(*args, **kwargs)
        self.scanner_name = PLUGIN_NAME
        self.scan = Scan.objects.get(pk=int(self.model_pk))
        self.do_configure()
        
    def do_configure(self):
        super(W3af, self).do_configure()
         
