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
        #Instantiating a model in now way touches your database; for that, you need to save()
        self.scan = kwargs.pop('scan', Scan(uniform_resource_locator='http://scanme.nmap.org')) 
        current_time = datetime.datetime.now()
         
        #Check if the zipfile exists in archive/ or another absolute path
        if not os.path.exists(self.scan.zip.name):
            self.temporary_folder_path = os.path.join(settings.TEMPORARY_DIR, self.scan.zip.name)
            self.file_list = list()                
            os.makedirs(self.temporary_folder_path)

    def track_file(self, absolute_path):
        if not absolute_path:
            return None
        try:
            assert not isinstance(absolute_path, basestring)
            assert not isinstance(absolute_path[0], str) or absolute_path[0]
            assert os.path.exists(absolute_path[0])
            assert absolute_path[1]
        except AssertionError as err:
            sys.exit(1)
        
        if not os.path.exists(self.temporary_folder_path):
            os.makedirs(self.temporary_folder_path)

        base_filename = os.path.basename(absolute_path[0])
        new_file_path = os.path.join( self.temporary_folder_path, base_filename )
        shutil.move( absolute_path[0], new_file_path )
        #Establish the file's relationship to the scan. 
        MetaFile(scan=self.scan, store=self.scan.zip, report=base_filename, success=False, role=absolute_path[1]).save()
        self.file_list.append(new_file_path)

    def archive_meta_files(self, file_list):
        """
        Zips the provided temporary files in settings.TEMPORARY_DIR by moving them to a folder
        and zipping the folder. Then, it deletes the original folder and moves the zip to
        the settings.ARCHIVE_DIR.

        file_list is a tuple contianing absolute file path and role of file.
        """
        if not file_list:
            return None
       
        for absolute_path in file_list:
            self.track_file(absolute_path)

        # default related_name is model name in lower case
        self.scan.zip.name = self.temporary_folder_path
         
        base_directory = os.path.basename(self.temporary_folder_path)
        root_directory = os.path.dirname(self.temporary_folder_path)
        #Zip the folder containing the meta files
        zip_folder_path = shutil.make_archive(base_name=self.temporary_folder_path, format='zip', root_dir=root_directory, base_dir=base_directory)
        self.scan.zip.name = os.path.join(settings.ARCHIVE_DIR, base_directory)

        #Move the zip folder to the archive path
        shutil.move(zip_folder_path, self.scan.zip.name)

        #Commit the changes to both models
        self.scan.zip.save()
        self.scan.save()

        #delete the pre-zip folder in temporary
        shutil.rmtree(self.temporary_folder_path)

    def unzip_file(self, file_list):
        """
        Unzip individual files from the archive and store the directory under temporary.
        Operates fine under succession.
        """
        individual_extraction_path = list()
        try:
            archive = zipfile.ZipFile(self.scan.zip.name, 'r')
            zip_basename = os.path.basename(self.scan.zip.name)
            for item in file_list:
                individual_extraction_path.append(archive.extract(os.path.join(zip_basename, item), settings.TEMPORARY_DIR))
        except (IOError, KeyError) as err:
            #There is no item named <item> in the archive.
            #No such file or directory
            return None

        return individual_extraction_path 
