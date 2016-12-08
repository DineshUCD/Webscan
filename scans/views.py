from django.shortcuts import render, reverse
from django.http import *

from scans.models import *
from scans.Zipper import *
from uploads.models import *
from scans.forms import *
from .tasks import *
from celery import chord
import uploads.views
import subprocess, os, sys

from webscanner.settings import *

# Create your views here.
def index(request):

    # sticks in a POST or renders empty form
    form = ScanForm(request.POST or None)

    context = {
        'form': form,
    }
    if form.is_valid():
        instance = form.save()

        zipper   = ZipArchive(scan=instance.id) 
        callback = collect_results.s()                           
        header   = [delegate.s(plugin_name, instance.id) for plugin_name in ['W3af', 'Gauntlt']]
        result   = chord(header)(callback).get()
        zipper.archive_meta_files(result)   
        
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
    return render(request, 'scans/index.html', context)
