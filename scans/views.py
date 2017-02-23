from django.shortcuts import render, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, generics
from rest_framework.response import Response

from scans.serializers import ScanSerializer

from scans.models import Scan
from uploads.models import Upload
from plans.models import Plan

from celery import chord, group
from .tasks import delegate, collect_results

# Create your views here.
# When deserializing data, we can either create a new instance, or update an existing one.
class ScanList(generics.ListCreateAPIView):
    serializer_class = ScanSerializer

    def get_queryset(self):
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
            print scan.task_id
            #Store group task results in appropriate tools. 
            #result.parent[#] gives appropriate task id in the order tasks were listed in group.
           

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ScanDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScanSerializer

    def get_queryset(self):
        queryset = Scan.objects.filter(user_profile__id=int(self.request.user.userprofile.id))
        return queryset

def launch(request, template_name='scans/index.html'):
    user_session = request.user.userprofile.get_latest_session()
    plan_pks = user_session.getitem('plan')

    context = dict()
  
    if plan_pks and isinstance(plan_pks, list):
        context['plans'] = Plan.objects.filter(pk__in=plan_pks, user_profile__id=int(request.user.userprofile.id)) 

    return render(request, template_name, context)
