from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, generics
from rest_framework.response import Response

from scans.serializers import ScanSerializer

from scans.models import Scan, Tool, PassFailTool, MetaFile
from uploads.models import Upload
from uploads.forms import UploadForm
from plans.models import Plan

from celery import chord, group
from .tasks import delegate, collect_results

from webscanner.settings import THREADFIX_URL

import sys, os
from datetime import datetime, timedelta

# Create your views here.
# When deserializing data, we can either create a new instance, or update an existing one.
class ScanList(generics.ListCreateAPIView):
    serializer_class = ScanSerializer

    def get_queryset(self):
        queryset = None
        if self.request.method == 'GET' and 'recent' in self.request.GET:
            queryset = Scan.objects.filter(user_profile__id=self.request.user.userprofile.id, date__gte=datetime.now()-timedelta(seconds=300))
        else:
            queryset = Scan.objects.filter(user_profile__id=int(self.request.user.userprofile.id))

        return queryset
            
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            scan = serializer.save()
            header = [delegate.s(tool.module, scan.id) for tool in scan.plan.tool_set.all()]
            result = (group(header) | collect_results.s(scan_identification=scan.id))()
            
            #Store Queue task id in Scan model & Save
            Scan.objects.filter(pk=scan.pk).update(task_id=str(result))
            scan.refresh_from_db()

            #Store group task results in appropriate tools. 
            #result.parent[#] gives appropriate task id in the order tasks were listed in group.
            for task_uuid, tool in zip(result.parent, scan.plan.tool_set.all()):
                Tool.objects.filter(pk=tool.pk).update(task_id=str(task_uuid))
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def launch(request, template_name='scans/index.html'):
    user_session = request.user.userprofile.get_latest_session()
    plan_pks = user_session.getitem('plan')

    context = dict()
  
    if plan_pks and isinstance(plan_pks, list):
        context['plans'] = Plan.objects.filter(pk__in=plan_pks, user_profile__id=int(request.user.userprofile.id)) 
    
    return render(request, template_name, context)

def detail(request, pk, template_name='scans/detail.html'): 
    scan = get_object_or_404(Scan, user_profile__id=int(request.user.userprofile.id), pk=pk)

    form = UploadForm(request.POST or None, { 'scan': scan})
    context = {
        'scan': scan,
        'form': form,
        'tools':list()
    }
    context['scan_state'] = scan.get_state()
    # Require tool name, tool files, and tool status
    tools = scan.plan.tool_set.all()
    num_metafiles = 0

    for tool in tools:  
        scan_files = tool.metafile_set.filter(role=MetaFile.SCAN)

        #Sum the number of scan metafiles all the tool(s) contain.
        num_metafiles = num_metafiles + scan_files.count()
        state = tool.get_state()

        # Structure the information for each tool.
        tool_information = { 'name': tool.name, 'state': state, 'files': scan_files }

        # Get pass/fail status if tool is of type PassFailTool
        if PassFailTool.objects.filter(pk=tool.pk).exists():
            test = tool.passfailtool.get_test()
            tool_information['test'] = test
       
        context['tools'].append(tool_information)

    context['num_metafiles'] = num_metafiles

    return render(request, template_name, context)

