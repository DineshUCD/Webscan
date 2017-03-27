from django.contrib import admin
from guardian.models import UserObjectPermission, GroupObjectPermission

# Register your models here.
classes = [GroupObjectPermission]
admin.site.register(classes)

