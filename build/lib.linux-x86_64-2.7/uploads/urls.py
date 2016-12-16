from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'uploads'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<upload_id>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/results/$', views.results, name='results'),
]
