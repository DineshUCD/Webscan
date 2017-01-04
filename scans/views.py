from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic.edit import UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from scans.serializers import PlanSerializer
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
    plan_pks = get_session_variable(request, 'add_scan')
    form = ScanForm(request.POST or None, plan_pks=plan_pks)

    context = {
        'form': form,
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user_profile = request.user.userprofile
        instance.save()
        
        # Validate primary keys in Controller

        plans    = map(int, form.cleaned_data['plan_pks'])
        tools    = Tool.objects.filter(plan__id__in=plans)
       
        modules  = list()
        for tool in tools:
            print tool.module
            modules.append(tool.module)

        #zipper   = ZipArchive(scan=instance.id) 
        callback = collect_results.s(scan_identification=instance.id)                           
        header   = [delegate.s(plugin_name, instance.id) for plugin_name in modules]
        result   = chord(header)(callback)
        #zipper.archive_meta_files(result)   
        
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
    return render(request, 'scans/index.html', context)

#Writing regular Django views using our Serializers
@api_view(['GET', 'POST'])
def plan_list(request, format=None):
    """
    List all plans, or create a new plan.
    """
    if request.method == 'GET':
        plans = Plan.objects.filter(user_profile__id=int(request.user.userprofile.id))
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PlanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
"""
@login_required(login_url='/accounts/login/')
def setup(request):

    form = PlanForm(request.POST or None, request=request)

    context = {
        'form' : form, 
        'plans': Plan.objects.filter(user_profile__id=int(request.user.userprofile.id)),
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user_profile = request.user.userprofile
        instance.save()
        plugin_choices = form.cleaned_data['plugins']
        #for plugin in plugin_choices:
            #Tool.objects.create(plan=instance, module=plugin)
    
        set_session_object(request, 'plugins', plugin_choices, set_session_variable)
        
    return render(request, 'scans/setup.html', context)

class PlanDelete(DeleteView):
    model = Plan
    success_url = reverse_lazy('scans:setup')
    template_name = 'scans/setup.html'
    
    def get_object(self, queryset=None):
        obj = get_object_or_404(Plan, user_profile__id=self.request.user.userprofile.id, pk= int(self.kwargs['pk']))
        return obj
        
class PlanUpdate(UpdateView):
    form_class = PlanForm
    model = Plan
    template_name = 'scans/setup.html'  

    def get_object(self, queryset=None):
        obj = get_object_or_404(Plan, user_profile__id=self.request.user.userprofile.id, pk= int(self.kwargs['pk']))
        return obj

    def get_success_url(self, *args, **kwargs):
        return reverse('scans:setup')

@login_required(login_url='/accounts/login')
def add_scan(request, plan_id):
    plan = get_object_or_404(Plan, user_profile__id=int(request.user.userprofile.id), pk=plan_id)
    if request.method == 'POST':
        if 'add_scan' in request.POST:
            set_session_object(request, 'add_scan', plan.id, set_session_list)
        elif 'unadd_scan' in request.POST:
            set_session_object(request, 'add_scan', plan.id, remove_from_session_list)

    return HttpResponseRedirect(reverse('scans:setup'))
"""
