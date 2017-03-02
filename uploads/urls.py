from django.conf.urls import include, url
from django.contrib import admin

from . import views
from . import Downloader

app_name = 'uploads'
urlpatterns = [ 
    url(r'list/$', views.UploadList.as_view(), name='upload-list'),
    url(r'deliver/$', Downloader.send_zipfile, name='deliver'),
]
