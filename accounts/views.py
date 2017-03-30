from django.shortcuts import render, render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.template import RequestContext
from django.core import urlresolvers
from django.http import HttpResponseRedirect

from scans.tasks import find_all_interfaces
from plans.models import Plan
from accounts.models import UserProfile, UserSession
from accounts.Group import Guardian
from webscanner.logger import logger

# Create your views here.
def register(request, template_name="registration/register.html"):
    if request.method == "POST":
        postdata = request.POST.copy()
        form     = UserCreationForm(postdata)
        if form.is_valid():
            form.save()
            un = postdata.get('username', '')
            pw = postdata.get('password1', '')
            from django.contrib.auth import login, authenticate
            new_user = authenticate(username=un, password=pw)
            if new_user and new_user.is_active:
                login(request, new_user)
                url = urlresolvers.reverse('scans:index')
                return HttpResponseRedirect(url)
    else: 
        form = UserCreationForm()
    page_title = 'User Registration'
    return render(request, template_name, locals())

@login_required(login_url='/accounts/login/')
def my_account(request, template_name="registration/my_account.html"):
    context = { }

    guardian = Guardian()
 
    context[ 'page_title' ]    ='Groups'
    context[ 'name' ]          = request.user.username
    context[ 'group_objects' ] = guardian.order_by_group(request.user)
        
    return render(request, template_name, context) 


def end(request, template_name="registration/logout.html"):
    """
    Invalidate the user's sessions and redirect the user to the login.
    """
    if request.user.is_authenticated():
        request.user.userprofile.invalidate_sessions()

    logout(request)

    return render(request, template_name, locals())
