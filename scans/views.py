from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.edit import UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics
from scans.serializers import PlanSerializer
from scans.models import *
from scans.Zipper import *
from accounts.models import *
from accounts.views import *
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
    user_session = request.user.userprofile.get_latest_session()
    plan_pks = user_session.getitem('plan')
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

        callback = collect_results.s(scan_identification=instance.id)                           
        header   = [delegate.s(plugin_name, instance.id) for plugin_name in modules]
        result   = chord(header)(callback)
        
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
    return render(request, 'scans/index.html', context)

#Writing regular Django views using our Serializers
@csrf_exempt
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

@api_view(['GET', 'PUT', 'DELETE'])
def plan_detail(request, pk, format=None):
    """
    Retrieve, update, or delete a plan.
    """
    try:
        plan = Plan.objects.filter(user_profile__id=int(request.user.userprofile.id), pk=pk)
    except Plan.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PlanSerializer(plan, many=True)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PlanSerializer(plan, data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
"""
def setup(request):


    form = PlanForm(request.POST or None)

    context = {
        'form' : form
        'plans': Plan.objects.filter(user_profile__id=int(request.user.userprofile.id)),
    }

    if form.is_valid():
        instance = form.save(commit = False)
        instance.userprofile = request.user.userprofile
        instance.save()

"""    

@login_required(login_url='/accounts/login')
def deploy_plan(request, plan_id):
    user_profile = request.user.userprofile
    user_session = request.user.userprofile.get_latest_session()
    plan = get_object_or_404(Plan, user_profile__id=int(user_profile.id), pk=plan_id)
    if request.method == 'POST':
        if 'deploy_plan' in request.POST:
            user_session.set_session(user_session.appenditem  , plan=plan.id) 
        elif 'undeploy_plan' in request.POST:
            user_session.set_session(user_session.unappenditem, plan=plan.id)
    return HttpResponseRedirect(reverse('accounts:dashboard'))
