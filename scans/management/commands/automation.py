from django.core.management import BaseCommand
from django.conf import settings

import configparser, os, sys

from scans.models import *

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):

#Show this when the user types help.
#help = "Type python manage.py automation..."

    def add_arguments(self, parser):
        parser.add_argument('scan')

    # A command must define handle()
    def handle(self, *args, **options):
        scan_id = int(options['scan'])
        scan    = Scan.objects.get(pk=scan_id)

        # Gets the current working directory from which manage.py is interpreted
        # All plugins in realtion to current working directory
        # E.x. /home/djayasan/Documents/webscanner
        current_working_directory = os.getcwd()
       
        # Read the list of local plugins from config.ini 
        plugins_configuration = configparser.ConfigParser()
        plugins_configuration.read( os.path.join(settings.PLUGINS_DIR, 'config.ini') )
        
