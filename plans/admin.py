from django.contrib import admin
from .models import Plan

# Register your models here.
classes = [Plan]
admin.site.register(classes)
