from django.shortcuts import render
from django.http import *

from scans.models import *
from uploads.models import *
from scans.forms import *
import uploads.views
import subprocess, os, sys


# Create your views here.
def index(request):


    # No need for an instance here
    # sticks in a POST or renders empty form
    form = ScanForm(request.POST or None)

    context = {
        'form': form,
    }

    if form.is_valid():
        # Save a new Scan from the form's data.
        instance = form.save()

        subprocess.call("python manage.py automation " + str(instance.id), shell=True)
         
        if instance.application_id != -1:
	    context['instance'] = instance
            return uploads.views.index(request, context)			
`
    return render(request, 'scans/index.html', context)
