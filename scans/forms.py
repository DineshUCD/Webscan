from django import forms
from django.http import HttpResponse
from django.utils import html

from threadfix_api import threadfix

import configparser, requests, json, os, sys
from webscanner.settings import *
from requests.exceptions import *
from urllib2 import urlopen
from .models import Scan, MetaFile, Zip, Tool, Plan
from .tasks import find_all_interfaces, find_interface

#from webscanner.logger import logger
import logging
logger = logging.getLogger('scarab')
"""
To Do: Append list of available scans from cookies to this form.
Method: Pass in user cookie dictionary to form through kwargs,
Should we pass in the request object or the primary keys themselves?

"""
class ScanForm(forms.ModelForm):
    class Meta:
        model  = Scan
        fields = [ 'uniform_resource_locator', 'application_id' ]

    def __init__(self, *args, **kwargs):
        plan_pks = kwargs.pop('plan_pks', None) # Remove it from the stack. Do not pass to super...
        super(ScanForm, self).__init__(*args, **kwargs)
        
        
        if not plan_pks or not isinstance(plan_pks, list): 
            logger.error("Scan plan missing tool selection.")
        else:
            plans        = Plan.objects.filter(pk__in=plan_pks)
            PLAN_CHOICES = tuple( [ (plan.id, str(plan)) for plan in plans ] )
       
            # Place in format (primary key of Plan, Plan's unicode name) inside CHOICES tuple 
            self.fields['plan_pks'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=PLAN_CHOICES)
       
        information = list()
        CHOICES     = list() 
        
        #Get /threadfix/rest/teams data from Threadfix
        #If the response status code is not 200 OK, then return an empty choice list.
        try:
            # /rest/teams/ Get All Teams
	    #threadfix_response = requests.get("https://devo-ssc-01.eng.netsuite.com/threadfix/rest/teams/?apiKey=9ip21QrkHG4royNF0Rw8MMOeLZH7sPzQPYRn0TUwQtc", verify=False)
            threadfix_response = requests.get(THREADFIX_URL + "rest/teams/?apiKey=" + THREADFIX_API_KEY, verify=False)
        except (HTTPError, ConnectionError, Timeout) as e:
            logger.error(e.message)#.replace( '?apiKey=' + THREADFIX_API_KEY, '' ))                        
            self.fields['application_id'].widget.attrs['readonly'] = True
            self.fields['application_id'].widget.attrs['disabled'] = True
            return None

        logger.info("Successful connection to " + THREADFIX_URL + "rest/teams")

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
        plan_selections          = cleaned_data.get('plan_pks')
        status_code              = urlopen(uniform_resource_locator).code

        if not plan_selections:
            raise forms.ValidationError("You must select an appropriate scan plan at /scan/setup/.")
        elif len(plan_selections) > 1:
            raise forms.ValidationError("You may not select more than one at a time!")
        
        if (status_code / 100 >= 4):
            raise forms.ValidationError("URL " + uniform_resource_locator + " is not available.")

       # Verify for Valid Threadfix Request Parameters
          
    
        return cleaned_data

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PlanForm, self).__init__(*args, **kwargs)

        CHOICES = tuple(find_all_interfaces())
        if all(CHOICES): 
            self.fields['plugins'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=CHOICES)

    def clean(self):
        cleaned_data = super(PlanForm, self).clean()
        
        plugin_choices = cleaned_data.get('plugins')
        
        Tool.objects.filter(plan__id=self.instance.id).delete()
       
        if not self.instance.user_profile: 
            self.instance.user_profile = self.request.user.userprofile

        self.instance.save()

        for plugin in plugin_choices:
            Tool.objects.create(plan=self.instance, module=plugin)

        return cleaned_data
