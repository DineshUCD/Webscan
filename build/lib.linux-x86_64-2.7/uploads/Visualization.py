#!/usr/bin/env python
from scans.models import *
from django.conf import settings
from django.core.exceptions import *


import datetime, os, sys, json



class DndTree():

    def __init__(self, *args, **kwargs):
        self.tree = { "name": "User", "children": [] }

        # Get all the Scan history
        application_ids = Scan.objects.values_list('application_id', flat=True).distinct()
        
        for choice_number in application_ids:
            self.tree["children"].append( {"name": str(choice_number), "children": [] } )

        # Get unique application ids
        for choice_number in range(len(self.tree["children"])):
            #Get scans containing an application id
            scans = Scan.objects.filter( application_id = int(self.tree["children"][choice_number]["name"]) ) 
            #Loop through each scan
            for scan in scans:
                scan_detail = scan.get_scan_data()
                name_size = [ ]
                for point in scan_detail['output']:
                    name_size.append( {"name": point, "size":5000} )
                self.tree["children"][choice_number]["children"].append({ "name": os.path.basename(scan_detail["zip path"]) , "children": name_size }) 


        print json.dumps(self.tree)
