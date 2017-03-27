from django.contrib import admin
from .models import Tool, PassFailTool, Scan
# Register your models here.
classes = [Tool] # iterable list
admin.site.register(classes)
