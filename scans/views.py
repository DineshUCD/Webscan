from django.shortcuts import render
from django.http import *

from scans.models import *
from scans.forms import *

import subprocess, os, sys
import pickle

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
         
        # Upload to ThreadFix as well.
        if instance.team_id != -1:
            pass

    return render(request, 'scans/index.html', context)
