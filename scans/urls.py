from django.conf.urls import include, url
from django.views.generic import TemplateView

from django.contrib import admin

from . import views

app_name = 'scans'
urlpatterns = [
    url(r'^list/$', views.ScanList.as_view(), name='scan-list'),
    url(r'^history/$', TemplateView.as_view(template_name="scans/history.html"), name='scan-history'),
    url(r'^(?P<pk>[0-9]+)/detail/$', views.detail, name='detail'),
    url(r'^$', views.launch, name='index'),
]
