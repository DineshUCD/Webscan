from django.conf.urls import include, url
from django.views.generic import UpdateView

from django.contrib import admin

from . import views

app_name = 'scans'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^plans/$', views.plan_list, name='plan_list'),
    url(r'^plans/(?P<pk>[0-9]+)$', views.plan_detail, name='plan_detail'),
    #url(r'^setup/$', views.setup, name='setup'),
    #url(r'^(?P<pk>[\w-]+)/delete/$', views.PlanDelete.as_view(), name='delete'),
    #url(r'^(?P<pk>[\w-]+)/edit/$', views.PlanUpdate.as_view(), name='edit'),
    url(r'^(?P<plan_id>[0-9]+)/add_scan/$', views.deploy_plan, name='deploy_plan'),

]
