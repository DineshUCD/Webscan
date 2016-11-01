from webscanner.settings import *
from threadfix_api import threadfix
from multiprocessing import *

import time, os, datetime, json, requests, urllib2

def now():
    return str(time.asctime(time.localtime(time.time())))

class Uploader():

    verbose = False
    showDebugInfo = False

    def __init__(self, *args, **kwargs):
        """
        Takes an Upload model and performs only ThreadFix upload using its operations.
        
        """
        self.scan = kwargs.pop('scan', Scan(uniform_resource_locator='http://scanme.nmap.org'))
        current_time = now()
        self.tf = threadfix.ThreadFixAPI(THREADFIX_URL, THREADFIX_API_KEY, verify_ssl=False)
        self.repository = list()


    def add_file(self, path, application_id=-1):
        if not os.path.isfile(path):
            return None

        try:
            with open(path) as file:
                pass
        except IOError:
            sys.exit(1)
        finally:
            self.repository.append( (application_id, path) )
            return True

    def upload_scan(self, application_id, path):
        try:
            response_wrap = { 'file': path, 'application id': application_id }
            threadfix_response = tf.upload_scan(application_id=application_id, file_path=path)
        except (IOError, TimeoutError) as upload_error:
            response_wrap['upload error'] = upload_error
            return response_wrap
        else:
            response_wrap['threadfix response'] = threadfix_response
            return response_wrap

    def check_response(self, response_wrap):
        try:
            upload_error = response_wrap['upload error']
        except KeyError as other_error:
            threadfix_response = response_wrap['threadfix response']
            if threadfix_response.message != "":
                pass
        else:
            pass
       

    def upload_scans(self):
        pool_responses = list()

        pool = Pool(len(self.repository))
        
        for item in self.repository:
            pool_responses.append(pool.apply_async(upload_scan, item, callback=check_response))

        pool.close()
        pool.join()
  
        for worker in pool._pool:
            assert not worker.is_alive()

        return map(lambda pool_response: pool_response.get(), pool_responses)
        

