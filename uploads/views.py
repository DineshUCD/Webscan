from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response, reverse

from rest_framework import status, generics
from rest_framework.response import Response

from scans.models import Scan
from scans.Zipper import ZipArchive

from uploads.models import Upload
from uploads.Uploader import upload_scans
from uploads.Visualization import DndTree

from uploads.serializers import UploadSerializer

from webscanner.logger import logger 


class UploadList(generics.ListCreateAPIView):
    serializer_class = UploadSerializer
    
    def get_queryset(self):
        queryset = Upload.objects.filter(scan__user_profile__id=self.request.user.userprofile.id)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            upload = serializer.save()
             
            application_id = request.data.get('application_id', None)
            resources = list()
            for resource in request.data.get('resources', []):
                resources.append(resource)
            scan_pk = request.data.get('scan', None)
            context = dict() 
            if Scan.objects.filter(pk=scan_pk, user_profile__id=self.request.user.userprofile.id).exists():
                archive = ZipArchive(scan=scan_pk)
                unzipped = archive.unzip(resources)
                archive.close()
                upload_response = upload_scans(unzipped, application_id)
                context['upload_response'] = upload_response                
            return Response(context, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
