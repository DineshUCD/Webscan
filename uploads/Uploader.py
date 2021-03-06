#!usr/bin/env python

from webscanner.settings import *
from threadfix_api import threadfix
from multiprocessing import *

import time, os, datetime, json, requests, urllib2


def upload_scan(application_id, path):
    try:
        response_wrap = { 'file': path, 'application_id': application_id }
        tf = threadfix.ThreadFixAPI(THREADFIX_URL, THREADFIX_API_KEY, verify_ssl=False)
        threadfix_response = tf.upload_scan(application_id=application_id, file_path=path)
    except (IOError, TimeoutError) as upload_error:
        response_wrap['upload_error'] = upload_error
        return response_wrap
    else:
        response_wrap['threadfix_response'] = threadfix_response.message
        return response_wrap

def check_response(response_wrap):
    try:
        upload_error = response_wrap['upload_error']
    except KeyError as other_error:
        threadfix_response = response_wrap['threadfix_response']
        if threadfix_response != "":
            pass
    else:
        pass
   
       
def upload_scans(repository, application_id):
    pool = Pool(len(repository))
    pool_responses = list()
    for item in repository:
        pool_responses.append(pool.apply_async(upload_scan, (application_id, item,), callback=check_response))
    
    pool.close()
    pool.join()

    for worker in pool._pool:
        assert not worker.is_alive()

    threadfix_responses = map(lambda pool_response: pool_response.get(timeout=30), pool_responses)  
    return threadfix_responses         
