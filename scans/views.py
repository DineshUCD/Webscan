from django.shortcuts import render, reverse
from django.http import *

from scans.models import *
from uploads.models import *
from scans.forms import *
from .tasks import *
import uploads.views
import subprocess, os, sys

from webscanner.settings import *

# Create your views here.
def index(request):

    # No need for an instance here
    # sticks in a POST or renders empty form
    form = ScanForm(request.POST or None)

    context = {
        'form': form,
    }
#    result = add.delay()
 #   print result.get()
    if form.is_valid():
        # Save a new Scan from the form's data.
        instance = form.save()

        subprocess.call("python manage.py automation " + str(instance.id), shell=True)
         
        if instance.application_id != -1:
            upload = Upload.objects.create(scan=instance, uniform_resource_locator=THREADFIX_URL)
            # Always return an HTTPResponseRedirect after successfully dealing with POST data.
            # This prevents data from being posted twice if a user hits the Back button.
	    return HttpResponseRedirect(reverse('uploads:results', args=(upload.id, )))
            
            			

    return render(request, 'scans/index.html', context)
