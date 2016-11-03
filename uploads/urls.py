from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'uploads'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<upload_id>[0-9]+)/results/$', views.results, name='results'),
]
