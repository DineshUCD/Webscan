import inspect, logging, os, sys, uuid, abc, subprocess, configparser, traceback, json

from django.conf import settings
from webscanner.settings import *
from webscanner.logger import logger
from scans.models import *

class Summary:

    """
    Create standardized glossary of terms:

    """
    def __init__(self, *args, **kwargs):
        
        # Get the stack frame at depth 1. Returns None if class name not available.
        try:
            caller = sys._getframe(1).f_locals['self'].__class__.__name__
        except KeyError as e:
            caller = None

        self.plugin   = kwargs.pop('plugin', caller)

        diagnostics = dict()
        diagnostics[self.plugin] = dict()
        self.json_str = diagnostics

    def appenditem(key, value):
        if not key in self.json_str or not type(self.json_str) is list:
            self.json_str[key] = list()

        self.json_str[key].append(value)

    def setitem(key, value):
        self.json_str[key] = value

    def getinfo():
        return self.json_str
        
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
        # This is in JSON format for extensibility. 
        self.output   = dict() 
        # Stores the output of the plugin execution.
        self.standard_output = None
         
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
            self.temporary_folder_path = os.path.join( settings.TEMPORARY_DIR, self.model.zip.name )
            if not os.path.exists(self.temporary_folder_path):
                os.makedirs(self.temporary_folder_path)
        except (Scan.DoesNotExist, OSError) as e:
            return None

    @abc.abstractmethod
    def do_stop(self):
        return self.meta_files

    # super().spawn() climbs the class hierarchy and returns the correct class that shall be called.
    def spawn(self,  arguments):
        if not arguments:
            return None

        try: 
            sts = subprocess.Popen(arguments, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.standard_output = sts.stdout.readlines()
            sts.stdout.close() 
            sts.stderr.close()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.standard_output = None
            return None

    def __repr__(self):
        return json.dumps(self.__dict__)
