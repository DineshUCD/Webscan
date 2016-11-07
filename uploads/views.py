from django.shortcuts import get_object_or_404, render
from django.db.models import F
from django.http import *

from scans.models import *
from scans.Zipper import *

from uploads.models import *
from uploads.forms import *
from uploads.Uploader import *
from uploads.Visualization import *

from webscanner.logger import logger 

import datetime, subprocess, os, sys

# Create your views here.
def index(request):
    """
    Collect all the Scan Results for a user, display previews of a selected scan,
    and redirect the user to the results upload page.    
    """
    scans = Scan.objects.all()
    
    return render(request, 'uploads/index.html')


def results(request, upload_id):
    upload = get_object_or_404(Upload, pk=upload_id)
    threadfix_items = upload.scan.get_scan_data()['output']
    form = ResultForm(request.POST or None, scan_results=threadfix_items)
    viz = DndTree()
    context = {
        'form': form,
    }

    if form.is_valid():
        upload_choices = form.cleaned_data['scan_results']
        archive = ZipArchive(scan=upload.scan)
        scan_unzip_files = archive.unzip_file(upload_choices)
        repository = list()
        add_files(repository, scan_unzip_files, 4)
        upload_response = upload_scans(repository)
        context['upload_response'] = upload_response
       

    return render(request, 'uploads/results.html', context)

    
