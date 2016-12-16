from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'scans'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^setup/$', views.setup, name='setup'),
]
