import logging, os, sys, subprocess, configparser

from django.conf import settings
from webscanner.plugin_api import *
from scans.models import *

class W3af(AbstractPlugin):
    PLUGIN_NAME = "W3af"
    PLUGIN_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        super(W3af, self).__init__(*args, **kwargs)
        self.do_configure()
        
    def do_configure(self):
        super(W3af, self).do_configure()

        # Configure W3af
        w3af_parameters = { 'url': str(model.uniform_resource_locator), 'path': self.zipper_path }
        try:
            w3af_template = pllugins_configuration['APPLICATIONS']['w3af_template']
        except KeyError as key:
            self.w3af_script_file_path=''
        else:
            self.w3af_script_file_path = os.path.join( self.zipper_path, 'w3af_script.w3af' )
            
                
