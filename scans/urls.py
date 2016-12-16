from django.conf.urls import include, url
from django.views.generic import UpdateView

from django.contrib import admin

from . import views

app_name = 'scans'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^setup/$', views.setup, name='setup'),
    url(r'^(?P<plan_id>[0-9]+)/delete/$', views.delete, name='delete'),
    url(r'^(?P<pk>[\w-]+)/edit/$', views.PlanUpdate.as_view(), name='edit'),
    url(r'^(?P<plan_id>[0-9]+)/add_scan/$', views.add_scan, name='add_scan'),

]
