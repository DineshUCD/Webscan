import logging, os, sys, uuid, abc, subprocess, configparser

from django.conf import settings

class AbstractPlugin:

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

    Plugin that spawns an external tool.
    """

    @classmethod
    def name(cls):
        return getattr(cls, "PLUGIN_NAME", cls.__name__)

    @classmethod
    def version(cls):
        return getattr(cls, "PLUGIN_VERSION", "0.0")

    def __init__(self, *args, **kwargs):
        self.program_name = kwargs

    def locate_program(self, program_name):
        if not program_name or not configuration:
            return None

        for path in os.getenv('PATH').split(os.pathsep):
            program_path = os.path.join(path, program_name)
        
            if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
                return program_path


    

    def do_configure(self):
        scanner_path = self.locate_program(
