from django.shortcuts import render, reverse
from django.contrib.auth.decorators import login_required
from django.http import *

from scans.models import *
from scans.Zipper import *
from accounts.models import *
from uploads.models import *
from scans.forms import *
from .tasks import *
from celery import chord
import uploads.views
import subprocess, os, sys

from webscanner.settings import *

# Create your views here.
@login_required(login_url='/accounts/login/')
def index(request):

    # sticks in a POST or renders empty form
    form = ScanForm(request.POST or None)

    context = {
        'form': form,
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user_profile = request.user.userprofile
        instance.save()

        zipper   = ZipArchive(scan=instance.id) 
        callback = collect_results.s()                           
        header   = [delegate.s(plugin_name, instance.id) for plugin_name in ['w3af_console', 'gauntlt']]
        result   = chord(header)(callback).get()
        zipper.archive_meta_files(result)   
        
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
    return render(request, 'scans/index.html', context)

@login_required(login_url='/accounts/login/')
def setup(request):
    form = PlanForm(request.POST or None)
    context = {
        'form': form, 
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user_profile = request.user.userprofile
        instance.save()
       
        plugin_choices = form.cleaned_data['plugins']
        for plugin in plugin_choices:
            Tool.objects.create(plan=instance, module=plugin)

        set_session_dictionary(request, 'plugins', plugin_choices)

        context['instance'] = instance
        
    return render(request, 'scans/setup.html', context)
