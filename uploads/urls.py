from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'uploads'
urlpatterns = [ 
    url(r'list/$', views.UploadList.as_view(), name='upload-list'),
]
