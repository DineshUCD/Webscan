import logging, os, sys, subprocess, configparser, yaml

from django.conf import settings
from webscanner.plugin_api import *
from webscanner.logger import logger
from scans.models import *

class Gauntlt(AbstractPlugin):
    PLUGIN_NAME = "gauntlt"
    PLUGIN_VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        super(Gauntlt, self).__init__(*args, **kwargs)
        #Call subclass's specific implementations of superclass's methods
        self.do_configure()
        
    def do_configure(self):
        super(Gauntlt, self).do_configure(Gauntlt.PLUGIN_NAME)
      
        temporary_folder_path = os.path.join( settings.TEMPORARY_DIR, self.model.zip.name )
        
        #Configure Gauntlt

        #Editing the config\cucumber.yml file. A basic cucumber profile may consist of a 'default profile.'
        #By default, Gauntlt will search in the current folder and its subfolders for files with the attack extension.
        #Input: config/cucumber.yml and plugins/attack/*.attack
        #Output: temporary/arachni_tests.afr, temporary/arachni_tests.xml <- Change in cucumber.yml

        # Write out to cucumber.yml first
        gauntlt_yaml_configuration = "CURRENT_DIRECTORY=" + str( temporary_folder_path ) + " URL=" + str( self.model.uniform_resource_locator )
        cucumber_profile_file_path = os.path.join(settings.CONFIG_DIR, 'cucumber.yml')
        self.meta_files.append((cucumber_profile_file_path, MetaFile.DOCUMENTATION))
        self.meta_files.append((os.path.join(temporary_folder_path, 'arachni_tests.xml'), MetaFile.SCAN))
        self.meta_files.append((os.path.join(temporary_folder_path, 'arachni_tests.afr'), MetaFile.DOCUMENTATION))
       
        with open(cucumber_profile_file_path, 'w') as cucumber_profile:
            cucumber_profile.write(yaml.dump(dict(default=gauntlt_yaml_configuration), default_flow_style=False))
        
        # End configuration of gauntlt

    def do_start(self):
        arguments = self.scanner_path
        super(Gauntlt, self).spawn(arguments)
        return self.do_stop()

    def do_stop(self):
        return super(Gauntlt, self).do_stop() 