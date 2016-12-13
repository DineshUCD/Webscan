from django.shortcuts import render, render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core import urlresolvers
from django.http import HttpResponseRedirect



# Create your views here.
def register(request, template_name="registration/register.html"):
    if request.method == "POST":
        postdata = request.POST.copy()
        form     = UserCreationForm(postdata)
        if form.is_valid():
            form.save()
            un = postdata.get('username', '')
            pw = postdata.get('password1', '')
            print un
            print pw
            from django.contrib.auth import login, authenticate
            new_user = authenticate(username=un, password=pw)
            print new_user
            if new_user and new_user.is_active:
                login(request, new_user)
                url = urlresolvers.reverse('accounts:my_account')
                return HttpResponseRedirect(url)
    else: 
        form = UserCreationForm()
    page_title = 'User Registration'
    return render(request, template_name, locals())

@login_required(login_url='/accounts/login/')
def my_account(request, template_name="registration/my_account.html"):
    page_title='My Account'
    name = request.user.username
    return render(request, template_name, locals()) 

@login_required(login_url='/accounts/login/')
def my_dashboard(request, template_name="dashboard/index.html"):
    return render(request, template_name, locals())
 
