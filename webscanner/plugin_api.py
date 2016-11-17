import logging, os, sys, uuid, abc, subprocess, configparser

from django.conf import settings

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
        self.scanner_name = kwargs.pop('scanner name', None)
        self.child_stdout = None
         
    def locate_program(self, program_name):
        if not program_name or not configuration:
            return None

        for path in os.getenv('PATH').split(os.pathsep):
            program_path = os.path.join(path, program_name)
        
            if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
                return program_path

    @abc.abstractmethod
    def do_configure(self):
        scanner_path = self.locate_program(self.scanner_name)
        if not scanner_path:
            raise Exception("Cannot find scanner program.")

    # super().spawn() climbs the class hierarchy and returns the correct class that shall be called.
    def spawn(self,  arguments):
        if not arguments:
            return None
        p = subprocess.Popen(arguments, shell=True, stdout=subprocess.PIPE, close_fds=True)
        self.child_stdout = p.stdout
