import logging, os, sys, subprocess, configparser

from django.conf import settings
from webscanner.plugin_api import *
from webscanner.logger import logger
from scans.models import *

class W3af(AbstractPlugin):
    PLUGIN_NAME = "w3af_console"
    PLUGIN_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        super(W3af, self).__init__(*args, **kwargs)
        #Initialize subclass's specific public scope variables.
        self.w3af_script_file_path = ''
        #Call subclass's specific implementations of superclass's methods
        self.do_configure()
        
    def do_configure(self):
        super(W3af, self).do_configure(W3af.PLUGIN_NAME)

        plugins_configuration = configparser.ConfigParser()
        plugins_configuration.read( os.path.join( settings.PLUGINS_DIR, 'config.ini' ) )
      

        # Configure W3af
        #Store w3af output file in temporary/w3af_resultzs.xml
        #Store w3af script in temporary/w3af_script.w3af
        #The stored w3af configuration script is in plugins/config.ini
        w3af_parameters = { 'url': str(self.model.uniform_resource_locator), 'path': self.temporary_folder_path }
        try:
            w3af_template = plugins_configuration['APPLICATIONS']['w3af_template']
        except KeyError as key:
            logger.warn("Unable to find w3af script configuration template for " + W3af.PLUGIN_NAME + ".")   
        else:
            self.w3af_script_file_path = os.path.join( self.temporary_folder_path, 'w3af_script.w3af' )
            self.meta_files.append( (self.w3af_script_file_path                                  , MetaFile.DOCUMENTATION) )
            self.meta_files.append( (os.path.join(self.temporary_folder_path, 'w3af_results.xml'), MetaFile.SCAN         ) )
            
            with open(self.w3af_script_file_path, 'w') as w3af_script:
                w3af_script.write( str(w3af_template.format(**w3af_parameters)) )
        # End configuration of W3af

    def do_start(self):
        arguments = self.scanner_path + ' -s ' + self.w3af_script_file_path
        print arguments
        super(W3af, self).spawn(arguments)
        return self.do_stop()

    def do_stop(self):
        return super(W3af, self).do_stop() 

