from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import *
from django.views.generic.edit import UpdateView
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
        'form' : form, 
        'plans': Plan.objects.filter(user_profile__id=int(request.user.userprofile.id)),
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user_profile = request.user.userprofile
        instance.save()
        plugin_choices = form.cleaned_data['plugins']
        for plugin in plugin_choices:
            Tool.objects.create(plan=instance, module=plugin)
    
        set_session_object(request, 'plugins', plugin_choices, set_session_variable)
        
    return render(request, 'scans/setup.html', context)

@login_required(login_url='/accounts/login/')
def delete(request, plan_id):
    plan = Plan.objects.filter(user_profile__id=int(request.user.userprofile.id)).get(pk=plan_id)
    if request.method == 'POST':
        if 'delete' in request.POST:
            plan.delete()
        else:
            pass           
    return HttpResponseRedirect(reverse('scans:setup'))

class PlanUpdate(UpdateView):
    form_class = PlanForm
    model = Plan
    template_name = 'scans/setup.html'  

    def get_object(self, queryset=None):
        obj = get_object_or_404(Plan, pk=self.kwargs['pk'])
        return obj

    def get_success_url(self, *args, **kwargs):
        return reverse('scans:setup')

@login_required(login_url='/accounts/login')
def add_scan(request, plan_id):
    plan = get_object_or_404(Plan, user_profile__id=int(request.user.userprofile.id), pk=plan_id)
    print 'add_scan' in request.POST    
    if request.method == 'POST':
        if 'add_scan' in request.POST:
            set_session_object(request, 'add_scan', plan.id, set_session_list)
        elif 'unadd_scan' in request.POST:
            set_session_object(request, 'add_scan', plan.id, remove_from_session_list)

    return HttpResponseRedirect(reverse('scans:setup'))
