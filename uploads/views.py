from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import *

from accounts.models import *

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

@login_required(login_url='/accounts/login')
def results(request, upload_id):
    #upload_primary_key = Upload.objects.filter(scan__user_profile__id = int(request.user.userprofile.id), id = int(upload_id))

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
        scan_unzip_files = archive.unzip_file(upload_choices)
        repository = list()
        add_files(repository, scan_unzip_files, upload_id)
        upload_response = upload_scans(repository)
        context['upload_response'] = upload_response
       

    return render(request, 'uploads/results.html', context)

    
