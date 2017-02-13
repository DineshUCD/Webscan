from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from scans.serializers import ScanSerializer, PlanSerializer

from scans.models import Scan, Plan, Tool
from uploads.models import Upload
from scans.forms import ScanForm
from celery import chord, group
from .tasks import delegate, collect_results

import subprocess, os, sys

from webscanner.settings import THREADFIX_URL
from webscanner.logger import logger

# Create your views here.
"""
@login_required(login_url='/accounts/login/')
def index(request):

    # sticks in a POST or renders empty form
    user_session = request.user.userprofile.get_latest_session()
    plan_pks = user_session.getitem('plan')
    form = ScanForm(request.POST or None, plan_pks=plan_pks)

    test = (group([add.s(4,4), add.s(4,5)]) | tsum.s())()

    context = {
        'form': form,
        'test': test
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
            modules.append(tool.module)
        
        header   = [delegate.s(plugin_name, instance.id) for plugin_name in modules]
        result   = (group(header) | collect_results.s(scan_identification=instance.id))()

        context['status'] = result.parent
 
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
    return render(request, 'scans/scans.html', context)
"""
# When deserializing data, we can either create a new instance, or update an existing one.
@csrf_exempt
@api_view(['GET', 'POST'])
def scan_list(request, format=None):
    """
    List all scans, or create a new scan for a user.
    """
    if request.method == 'GET':
        scans = Scan.objects.filter(user_profile__id=int(request.user.userprofile.id))
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)

    elif request.method == 'POST': 
        serializer = ScanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
   
            header = [delegate.s(tool.module, serializer.object.id) for tool in serializer.object.plan.tool_set.all()]
            result = (group(header) | collect_results.s(scan_identification=serializer.object.id))()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
         
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
