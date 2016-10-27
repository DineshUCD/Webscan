from django.core.management import BaseCommand
from django.conf import settings
from django.core.exceptions import *

import shutil, configparser, os, sys, datetime, yaml
from scandir import scandir
import fnmatch
from scans.models import *
from scans.Zipper import *

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):

#Show this when the user types help.
#help = "Type python manage.py automation..."

    def add_arguments(self, parser):
        parser.add_argument('scan')

    # A command must define handle()
    def handle(self, *args, **options):

        def find_file_in_directory(directory_path, plugin, configuration):
            if not os.path.isdir(directory_path) or not plugin:
                return None

            absolute_paths = list()

            try:
                absolute_paths.append(configuration['APPLICATIONS'][plugin])
            except KeyError as key:
                for root, dirs, files in os.walk(directory_path):
                    nested_level = root.split('/')
                    if len(nested_level) == 5:
                        del dirs[:]
                    # Perform actions with file here.
                    for name in files:
                        if fnmatch.fnmatch(name, plugin):
                            absolute_paths.append(os.path.join(root, name))
            else:
                return absolute_paths[0]

            if not absolute_paths:
                return None
            else:
                configuration['APPLICATIONS'][plugin] = absolute_paths[0]  # create
                with open( os.path.join(settings.PLUGINS_DIR, 'config.ini'), 'w') as cfgfile:
                    configuration.write(cfgfile)
                return absolute_paths[0]

        scan_id = int(options['scan'])
          
        try:
            scan = Scan.objects.get(pk=scan_id)
        except Scan.DoesNotExist:
            scan = None
            sys.exit(1)

        zipper = ZipArchive(scan=scan)

        # Gets the current working directory from which manage.py is interpreted
        # All plugins in realtion to current working directory
        # E.x. /home/djayasan/Documents/webscanner
        current_working_directory = os.getcwd()
       
        # Read the list of local plugins from config.ini 
        plugins_configuration = configparser.ConfigParser()
        plugins_configuration.read( os.path.join(settings.PLUGINS_DIR, 'config.ini') )

        # Store meta file absolute paths for archiving them after scans finish
        meta_files = list()

        #Configure w3af
        
        #Store w3af output file in temporary/w3af_results.xml
        #Store w3af script in temporary/w3af_script.w3af
        #Stored template in plugins/config.ini
        w3af_console = find_file_in_directory(settings.PLUGINS_DIR, 'w3af_console', plugins_configuration) 
        w3af_parameters = { 'url': str(scan.uniform_resource_locator), 'path': str(settings.TEMPORARY_DIR) }
        try:
            w3af_template = plugins_configuration['APPLICATIONS']['w3af_template']
        except KeyError as key:
            sys.exit(1)
        else:
            w3af_script_file_path = str(os.path.join(settings.TEMPORARY_DIR, 'w3af_script.w3af'))
            meta_files.append( (w3af_script_file_path, MetaFile.DOCUMENTATION) )
            meta_files.append( (str(os.path.join(settings.TEMPORARY_DIR, 'w3af_results.xml')), MetaFile.SCAN) )
            #meta_files.append( str(os.path.join(settings.PLUGINS_DIR, 'config.ini')) )
            with open(w3af_script_file_path, 'w') as w3af_script:
                w3af_script.write( str(w3af_template.format(**w3af_parameters)) )
        #End configuration of w3af


        #Configure Gauntlt

        #Editing the config\cucumber.yml file. A basic cucumber profile may consist of a 'default profile.'
        #By default, Gauntlt will search in the current folder and its subfolders for files with the attack extension.
        #Input: config/cucumber.yml and plugins/attack/*.attack
        #Output: temporary/arachni_tests.afr, temporary/arachni_tests.xml <- Change in cucumber.yml
        
        # Write out to cucumber.yml first
        gauntlt_yaml_configuration = "CURRENT_DIRECTORY=" + str(current_working_directory) + " URL=" + str(scan.uniform_resource_locator)
        cucumber_profile_file_path = str(os.path.join(settings.CONFIG_DIR, 'cucumber.yml'))
        meta_files.append( (cucumber_profile_file_path, MetaFile.DOCUMENTATION) )
        meta_files.append( (str(os.path.join(settings.TEMPORARY_DIR, 'arachni_tests.xml')), MetaFile.SCAN) )
        meta_files.append( (str(os.path.join(settings.TEMPORARY_DIR, 'arachni_tests.afr')), MetaFile.DOCUMENTATION) )
        with open(cucumber_profile_file_path, 'w') as cucumber_profile:
            cucumber_profile.write(yaml.dump(dict(default=gauntlt_yaml_configuration), default_flow_style=False))
         
        #End configuration of gauntlt
        os.system(w3af_console + " -s " + w3af_script_file_path)
        os.system('gauntlt')
         
        zipper.archive_meta_files(meta_files)
