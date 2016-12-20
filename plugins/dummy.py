import logging, os, sys, subprocess, configparser, yaml

from django.conf import settings
from webscanner.plugin_api import *
from webscanner.logger import logger
from scans.models import *

class Dummy(AbstractPlugin):
    PLUGIN_NAME = "ls"
    PLUGIN_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        super(Dummy, self).__init__(*args, **kwargs)
        #Call subclass's specific implementations of superclass's methods
        self.do_configure()
        
    def do_configure(self):
        super(Dummy, self).do_configure(Dummy.PLUGIN_NAME)
      
        temporary_folder_path = os.path.join( settings.TEMPORARY_DIR, self.model.zip.name )
        

    def do_start(self):
        super(Dummy, self).spawn(self.scanner_path)
        return self.do_stop()

    def do_stop(self):
        return super(Gauntlt, self).do_stop() 
