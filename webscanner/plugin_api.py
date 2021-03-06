import inspect, re, logging, os, sys, uuid, abc, subprocess, configparser, traceback, json

from django.conf import settings
from webscanner.settings import *
from webscanner.logger import logger
from scans.models import *

logger = logging.getLogger('scarab')


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
    FILES = "files"

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
        self.model = None
        #The tool that is associated with the scan's plugin.
        self.tool = None
        # The absolute path of the scanner executable; preferably, a console based program
        self.scanner_path = None
        # Stores the output of the plugin execution.
        self.standard_output = None
        # Stores the errors generated by the plugin
        self.standard_error = None
           
        self.class_name = self.__class__.__name__
 
        self.diagnostics = dict()
        # Stores meta data on the scan in json format.
        self.diagnostics[self.class_name] = dict()

    def set_metafile(self, absolute_file_path, role):
        filename = os.path.basename(absolute_file_path)
        metafile = MetaFile(scan=self.model, store=self.model.zip, tool=self.tool, report=filename, role=role).save()
        self.record(AbstractPlugin.FILES, [(absolute_file_path, role)])
        

    def record(self, key, value):
     
        if type(value) is list:
            if not key in self.diagnostics[self.class_name] or not type(self.diagnostics[self.class_name][key]) is list:
                self.diagnostics[self.class_name][key] = list()
            self.diagnostics[self.class_name][key].extend(value)
        else:
            self.diagnostics[self.class_name][key] = value
         
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
            self.tool = self.model.plan.tool_set.get(name=str(self.__class__.PLUGIN_NAME))
            self.temporary_folder_path = str(os.path.join( settings.TEMPORARY_DIR, self.model.zip.name ))
            if not os.path.exists(self.temporary_folder_path):
                os.makedirs(self.temporary_folder_path)
        except (Scan.DoesNotExist, Tool.DoesNotExist, OSError) as e:
            logger.error("Scan: {0}, Tool: {1}, Class: {2}, Other: {3}".format(str(self.model), str(self.tool), self.__class__, e))

    @abc.abstractmethod
    def do_stop(self):
        """
        Write standard output and standard error to files for execution reference.
        Treat both outputs as MetaFile.SCAN instead of documentation because
        plugins may be command line tools.
        """
        plugin_name = self.__class__.PLUGIN_NAME
        stdout = os.path.join(self.temporary_folder_path, str(plugin_name) + "stdout.txt")
        stderr = os.path.join(self.temporary_folder_path, str(plugin_name) + "stderr.txt")
        
        try:
            with open(stdout, 'w') as out:
                for output in self.standard_output:
                    out.write("%s" % output)

            with open(stderr, 'w') as err:
                for error in self.standard_error:
                    err.write("%s" % error)
        except EnvironmentError as e:
            logger.error(e)
           

        self.set_metafile(stdout, MetaFile.SCAN)
        self.set_metafile(stderr, MetaFile.SCAN)

        return self.diagnostics

    # super().spawn() climbs the class hierarchy and returns the correct class that shall be called.
    def spawn(self,  arguments):
        if not arguments:
            return None

        try: 
            sts = subprocess.Popen(arguments, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.standard_output = sts.stdout.readlines()
            self.standard_error  = sts.stderr.readlines()
            sts.stdout.close() 
            sts.stderr.close()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.standard_output = None
            return None

    def __repr__(self):
        return json.dumps(self.__dict__)

class Cli(AbstractPlugin):
    """
    Accept a command line tool supported in the webscanner/plugin directory and process its request.
    If the arguments are not empty, then we are dealing with a Cli
    """
    __metaclass__ = abc.ABCMeta
    
    #Override the do_configure on a per plugin basis.
    
    #Must pass tool model to attach configuration to command.

class Gauntlt(AbstractPlugin):
    """
    This class is used for quick pass/fail tests via the
    BDD framework. 
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do_configure(self):
        super(Gauntlt, self).do_configure("gauntlt")

    def test(self, check):
        if check is None:
            logger.error("Std Output: {0}, Check: {1}".format(check, self.standard_output))

        scenario = re.search("(\d+) scenarios?", check)
        scenario_count = int(scenario.group(1))
  
        passed = re.search("(\d+) passed", check)
        passed_count = 0

        if passed:
            passed_count = int(passed.group(1))
         
        failed = re.search("(\d) failed", check)
        failed_count = 0

        if failed:
            failed_count = int(failed.group(1))

        state = State.objects.get(scan=self.model, tool=self.tool)

        if failed_count == 0:
            state.test = True
        else:
            state.test = False
 
        state.save()
