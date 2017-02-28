from django import forms
from .models import Upload
from django.utils import html

from threadfix_api import threadfix
from webscanner.settings import THREADFIX_URL, THREADFIX_API_KEY

import configparser, requests, json, os, sys, logging

logger = logging.getLogger('scarab')

class UploadForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)

        information = list()
        CHOICES     = list()

        #Get /threadfix/rest/teams data from Threadfix
        #If the response status code is not 200 OK, then return an empty choice list.
        try:
            # /rest/teams/ Get All Teams
            threadfix_response = requests.get(THREADFIX_URL + "rest/teams/?apiKey=" + THREADFIX_API_KEY, verify=False)
        except (HTTPError, ConnectionError, Timeout) as e:
            logger.error(e.message)#.replace( '?apiKey=' + THREADFIX_API_KEY, '' ))                        
            self.fields['application_id'].widget.attrs['readonly'] = True
            self.fields['application_id'].widget.attrs['disabled'] = True
            pass

        logger.info("Successful connection to " + THREADFIX_URL + "rest/teams")

        #'empty_value'
        # Return a failed choice of empty, None if Django cannot reach Threadfix
        CHOICES.append( (-1, None) )

        if threadfix_response.status_code == 200:
            parsed_statistics = json.loads(threadfix_response.text)
            print parsed_statistics
            team_information  = parsed_statistics['object']
            if not parsed_statistics['success'] or not team_information:
                print "EXIT"
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


                
