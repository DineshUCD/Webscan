from django.conf.urls import include, url
from django.views.generic import UpdateView

from django.contrib import admin

from . import views

app_name = 'scans'
urlpatterns = [
    url(r'^list/$', views.ScanList.as_view(), name='scan-list'),
    url(r'^$', views.launch, name='index'),
]
