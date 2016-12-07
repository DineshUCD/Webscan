from django.core.management import BaseCommand
from django.conf import settings
from django.core.exceptions import *

import shutil, configparser, os, sys, datetime, yaml
from scandir import scandir
import fnmatch
from plugins.w3af import *
from plugins.gauntlt import *
from scans.models import *
from scans.Zipper import *
from webscanner.logger import logger
#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):

#Show this when the user types help.
#help = "Type python manage.py automation..."

    def add_arguments(self, parser):
        parser.add_argument('scan')

    # A command must define handle()
    def handle(self, *args, **options):

        scan_id = int(options['scan'])

        zipper = ZipArchive(scan=scan_id)
        meta_files = list()
        instance = W3af(model_pk=scan_id)
        gtlt     = Gauntlt(model_pk=scan_id) 

        #os.system(w3af_console + " -s " + w3af_script_file_path)
        w3af_list = instance.do_start()
        print w3af_list
        meta_files.extend(w3af_list)
        gauntlt_list = gtlt.do_start()
        meta_files.extend(gauntlt_list)
        print gauntlt_list
        print meta_files
        zipper.archive_meta_files(meta_files)
