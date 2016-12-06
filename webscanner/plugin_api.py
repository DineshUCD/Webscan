import logging, os, sys, uuid, abc, subprocess, configparser

from django.conf import settings
from scans.models import *

class AbstractPlugin(object):

    __metaclass__ = abc.ABCMeta

    """
    Abstract plugin implementation that implements a plugin's
    standard behavior, etc..
    Standard Behavior include:
        1. Spawning a subprocess with Popen
        2. Locating a program
        3. Tracking/Returning Metafiles
        4. Reporting progress, and other issues
    Standard information include:
        1. Version
        2. Plugin name
        3. Base Directory for executable

    """

    @classmethod
    def name(cls):
        return getattr(cls, "PLUGIN_NAME", cls.__name__)

    @classmethod
    def version(cls):
        return getattr(cls, "PLUGIN_VERSION", "0.0")

    # This is a concrete method; just invoke with super().__init__(*args, **kwargs)
    def __init__(self, *args, **kwargs):
        self.model_pk = kwargs.pop('model_pk', None)
        
        #The model that contains collects the Scan information
        self.model        = None
        # The absolute path of the scanner executable; preferably, a console based program
        self.scanner_path = None
        # Store the metafiles for each scan in a list and return it to view after the scan finishes
        self.meta_files   = list()

         
    def locate_program(self, program_name):
        if not program_name:
            return None

        for path in os.getenv('PATH').split(os.pathsep):
            program_path = os.path.join(path, program_name)
        
            if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
                return program_path

    @abc.abstractmethod
    def do_start(self):
        pass

    @abc.abstractmethod
    def do_configure(self, plugin_name):
        """
        Performs a scanner's common configuration such as locating it's executable
        and obtaining the model that interfaces with it. 
        
        No.7 Do not pass Database/ORM objects to tasks
        """
        self.scanner_path = self.locate_program(plugin_name)
        if not self.scanner_path:
            raise Exception("Cannot find scanner program.")

        try:
            self.model = Scan.objects.get(pk=int(self.model_pk))
        except Scan.DoesNotExist:
            sys.exit(1)

    @abc.abstractmethod
    def do_stop(self):
        return self.meta_files

    # super().spawn() climbs the class hierarchy and returns the correct class that shall be called.
    def spawn(self,  arguments):
        if not arguments:
            return None
        p = subprocess.Popen(arguments)
