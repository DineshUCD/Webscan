from django.shortcuts import get_object_or_404, render
from django.db.models import F

from scans.models import *
from uploads.models import *
from uploads.forms import *

import datetime, subprocess, os, sys

# Create your views here.
def index(request):
    return render(request, 'uploads/index.html')


def results(request, upload_id):
    upload = get_object_or_404(Upload, pk=upload_id)
    threadfix_items = upload.scan.get_scan_data()['output']
    form = ResultForm(request.POST or None, scan_results=threadfix_items)
    if form.is_valid():
        print form.cleaned_data
    return render(request, 'uploads/results.html', {'form': form})

    
