from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group, Permission

from scans.models import Scan
from accounts.models import UserProfile

# Create your models here.
class Plan(models.Model):
    # Each user profile saves zero or many scans.
    user_profile = models.ForeignKey(UserProfile, blank=True, null=True)
    # Each plan is associated with only one target URL vulnerability scan.
    scan         = models.OneToOneField(Scan, on_delete=models.CASCADE, null=True, blank=True)
    # Name of scan for client to identify them.
    name         = models.CharField(max_length=50, default="")
    created      = models.DateTimeField(auto_now_add=True)
    # Describes the motivation for each Plan.
    description  = models.CharField(max_length=256, default="", blank=True)

    # Restrict plans to users of certain groups
    class Meta:
        permissions = (
            ('view', 'View Plan'),
        )

    def __unicode__(self):
        return "{0} | {1}".format(self.name, self.description)
