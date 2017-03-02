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

from uploads.Downloader import extract_from_archival

from webscanner.logger import logger 

"""
@login_required(login_url='/accounts/login/')
def results(request, upload_id):

    upload = get_object_or_404(Upload, scan__user_profile__id=int(request.user.userprofile.id), id=upload_id)

    threadfix_items = upload.scan.get_scan_data()['output']
    form = ResultForm(request.POST or None, scan_results=threadfix_items)
    viz = DndTree()
    context = {
        'form': form,
    }

    if form.is_valid():
        upload_choices = form.cleaned_data['scan_results']
        archive = ZipArchive(scan=upload.scan.id)
        scan_unzip_files = archive.unzip(upload_choices)
        repository = list()
        add_files(repository, scan_unzip_files, upload.scan.application_id)
        upload_response = upload_scans(repository)
        context['upload_response'] = upload_response

    $return render(request, 'uploads/results.html', context)
"""

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
                unzipped = extract_from_archival(resources, scan_pk)
                upload_response = upload_scans(unzipped, application_id)
                context['upload_response'] = upload_response                
            return Response(context, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
