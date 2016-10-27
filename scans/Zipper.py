#!/usr/bin/env python

import zipfile, shutil, configparser, os, sys, datetime, fnmatch
from multiprocessing import Pool
from scans.models import *
from django.conf import settings
from django.core.exceptions import *


#Function names should be lowercase, with words separated by underscores as necessary to improve readability.

# BEGIN Utility Function definitions

#It works in memory and does not require the current working directory to be writable
def data_to_zip_direct(z, data, name):
    """
    Args: 
    z = zip file instance
    data = raw data in bytes
    name = string of the zip file name

    Returns:
    None if data or name is invalid

    Zips raw data in the current working directory with zip file name as 'name'.
    """
    import time

    if not data or not name:
        return None

    zinfo = zipfile.ZipInfo(str(name), time.localtime()[:6])
    z.writestr(zinfo, data)

def data_to_zip_indirect(z, data, name):
    import os

    if not z or not data or not name:
        return None

    flob = open(name, 'wb')
    flob.write(data)
    flob.close()
    z.write(name)
    os.unlink(name)

#traverse a folder tree and zip all the folders at a specific depth
def deep_folder_tree_zip(folders_to_zip, destination_directory=None):

    for folder in folders_to_zip:
        # get unique names for each zipped folder
        zipfile_name = "%s.zip" % (folder.replace("/", "_"))
        zfile        = zipfile.ZipFile( os.path.join(folder, zipfile_name), 'w', zipfile.ZIP_DEFLATED)
        
        # Use the length of the folder tree to designate where the folders need to be zipped from.
        root_length = len(folder) + 1
        for base, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(base, file)
                # zipped item name should be the filename                      
                zfile.write(file_path, file_path[root_length:])
        zfile.close()

    if destination_directory:
        shutil.move( os.path.join(folder, zipfile_name), destination_directory )


class ZipArchive():

    # If true then show some information about added files or directories
    verbose = False

    # If true then show some extra debug information
    showDebugInfo = False

    
    def __init__(self, *args, **kwargs):
        """
        Constructor with some extra parameters:
        * verbose: be detailed about what is happening. Defaults to True
        """ 
        #dict.pop() method removes the key from the dictionary, if present, 

        #returning the associated value or the default if missing
        self.verbose = kwargs.pop('verbose', True) 
        #Instantiating a model in now way touches your databasel for that, you need to save()
        self.scan    = kwargs.pop('scan', Scan(uniform_resource_locator='http://scanme.nmap.org')) 

                
    def archive_meta_files(self, file_list):
        """
        Zips the provided temporary files in settings.TEMPORARY_DIR by moving them to a folder
        and zipping the folder. Then, it deletes the original folder and moves the zip to
        the settings.ARCHIVE_DIR.

        file_list is a tuple contianing absolute file path and role of file.
        """
        """
        # BEGIN argument validation
        if not file_list:
            return None
       
        try:
            for file_tuple in file_list:
                assert not isinstance(file_tuple, basestring)
                assert not isinstance(file_tuple[0], str) or file_tuple[0]
                assert not os.path.exists(file_tuple[0])
                assert file_tuple[1]
        except AssertionError as assertion_error:
            sys.exit(1)
        # END argument validaiton
        """
        print "In function"
        print len(file_list)
        # default related_name is model name in lower case
        self.scan.zip.name = str(datetime.datetime.now()) + " " + str(self.scan).replace('http://', '', 1)
        print self.scan.zip.name 
        for absolute_path in file_list: 
            MetaFile(scan=self.scan, store=self.scan.zip, report=absolute_path[0], success=True, role=absolute_path[1]).save()
         
        zip_folder_name = os.path.join(settings.TEMPORARY_DIR, self.scan.zip.name)
        print zip_folder_name
        if not os.path.exists(zip_folder_name):
            os.makedirs(zip_folder_name)

        for absolute_path in file_list:
            shutil.move( absolute_path[0], os.path.join(zip_folder_name, absolute_path[0].split("/")[-1]) )
        
        #Zip the folder containing the meta files
        zip_folder_path = shutil.make_archive(zip_folder_name, 'zip', os.path.dirname(zip_folder_name), self.scan.zip.name)
        print zip_folder_path
        self.scan.zip.name   = os.path.join(settings.ARCHIVE_DIR, self.scan.zip.name)
	print self.scan.zip.name 

        #Move the zip folder to the archive path
        shutil.move(zip_folder_path, self.scan.zip.name)
        self.scan.save()

        #delete the pre-zip folder in temporary
        shutil.rmtree(zip_folder_name)
