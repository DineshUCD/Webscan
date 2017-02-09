from __future__ import unicode_literals

from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.timezone import utc

import datetime, sys, os, uuid

#Upload has a Many-to-Many relationship with Scan
from scans.models import Scan 

# Create your models here.
class Upload(models.Model):
    uniform_resource_locator = models.URLField(max_length=2083, blank=False, null=False)
    upload_date              = models.DateTimeField(auto_now=True)
    scan                     = models.ForeignKey(Scan, on_delete=models.CASCADE)
    # Univerally unique identifiers are a good alternative to AutoField for primary_key.
    id                       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def get_elapsed_time(self):
        if upload_date:
            # datetime.timedelta object returned
            # Django DateTimeField handles timezone aware datetime objects as well
            time_difference = datetime.datetime.utcnow().replace(tzinfo=utc) - self.upload_date
            return time_difference.total_seconds()

    def __unicode__(self):
        return "{0} @ {1} for {2}".format(self.status, self.uniform_resource_locator, self.scan.uniform_resource_locator)
