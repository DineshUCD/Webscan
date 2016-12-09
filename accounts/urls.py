from django.conf.urls import include, url
from django.contrib.auth.views import login
import django
from webscanner import settings

from accounts import views

app_name = 'accounts'
urlpatterns = [
    url(r'^register/$'  , views.register                 , {'template_name': 'registration/register.html' }, name='register'),
    url(r'^my_account/$', views.my_account               , {'template_name': 'registration/my_account.html'                           }, name='my_account'),
    url(r'^login/$'     , django.contrib.auth.views.login, {'template_name': 'registration/login.html'  }, name='login')
]
