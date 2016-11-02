from django import forms
from django.http import HttpResponse
from django.utils import html

from threadfix_api import threadfix

import configparser, requests, json, os, sys
from webscanner.settings import *
from requests.exceptions import *
from urllib2 import urlopen
from .models import Scan, MetaFile, Zip

class ScanForm(forms.ModelForm):
    class Meta:
        model  = Scan
        fields = [ 'uniform_resource_locator', 'application_id' ]

    def __init__(self, *args, **kwargs):
        super(ScanForm, self).__init__(*args, **kwargs)

        information = list()
        CHOICES     = list() 
        
        #Get /threadfix/rest/teams data from Threadfix
        #If the response status code is not 200 OK, then return an empty choice list.
        try:
            # /rest/teams/ Get All Teams
	    #threadfix_response = requests.get("https://devo-ssc-01.eng.netsuite.com/threadfix/rest/teams/?apiKey=9ip21QrkHG4royNF0Rw8MMOeLZH7sPzQPYRn0TUwQtc", verify=False)
            threadfix_response = requests.get(THREADFIX_URL + "/rest/teams/?apiKey=" + THREADFIX_API_KEY, verify=False)
        except (HTTPError, ConnectionError, Timeout) as e:
            threadfix_response = str(e)
            sys.exit(1)

        #'empty_value'
        # Return a failed choice of empty, None if Django cannot reach Threadfix
        CHOICES.append( (-1, None) )

        if threadfix_response.status_code == 200:
            parsed_statistics = json.loads(threadfix_response.text)

            team_information  = parsed_statistics['object']
            team_count        = len(team_information)


            #Gather each team's name, its applications, and respective application id. 
            #There exist one 'information' list entry per application id.
            for team in range(team_count):
	        team_name              = str(parsed_statistics['object'][team]['name'])
                team_application_count = len(parsed_statistics['object'][team]['applications'])
                for team_application in range(team_application_count):
                    application_id   = str(parsed_statistics['object'][team]['applications'][team_application]['id'])
                    application_name = str(parsed_statistics['object'][team]['applications'][team_application]['name'])
                    information.append([team_name, application_id, application_name])

            for application in information:
                CHOICES.append( (int(application[1]) , " | ".join((application[0], application[2]))) )
        # endif

        # Override the IntegerField in the Form to ChoiceField and pass the Integer in the tuple or the first argument to the Scan Model app id.
        self.fields['application_id'] = forms.ChoiceField(required=False, label="*Optional* Upload to Team App on Threadfix", choices=CHOICES)
        
    def clean(self):
        cleaned_data = super(ScanForm, self).clean()

        # Verify URL Exists.
        uniform_resource_locator = cleaned_data.get('uniform_resource_locator') 

        status_code              = urlopen(uniform_resource_locator).code
        if (status_code / 100 >= 4):
            raise forms.ValidationError("URL " + uniform_resource_locator + " is not available.")

       # Verify for Valid Threadfix Request Parameters
          
    
        return cleaned_data
