from django.shortcuts import render

from scans.models import *
from uploads.models import *

import subprocess, os, sys

# Create your views here.
def index(request, extra_context=None):
    if not extra_context:
        pass

    try:
        instance = extra_context['instance']
    except KeyError as invalid_model:
	pass
    
    
	
    return render(request, 'uploads/index.html', extra_context)
