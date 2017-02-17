from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'plans'
urlpatterns = [
    url(r'^$', views.my_plans, name='plans-list'),
    url(r'^create/$', views.PlanCreate.as_view(), name='plans-new'),
    url(r'^(?P<pk>[\w-]+)/edit/$', views.PlanUpdate.as_view(), name='plans-edit'),
    url(r'^(?P<pk>[\w-]+)/delete/$', views.PlanDelete.as_view(), name='plans-delete'),
    url(r'^(?P<pk>[0-9]+)/select/$', views.select, name='select'),
]
