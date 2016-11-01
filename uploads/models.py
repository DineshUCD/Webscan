from __future__ import unicode_literals

from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.timezone import utc

import datetime, sys, os
from webscanner.settings import *

#Upload has a Many-to-Many relationship with Scan
from scans.models import * 

# Create your models here.
class Upload(models.Model):
    PENDING         = 0
    DONE            = 1
    FAILED          = 2
    IDLE            = 3
    PARTIAL_FAILURE = 4
    STATUS_CHOICES = (
        (PENDING, 'PENDING'),
        (DONE, 'DONE'),
        (FAILED, 'FAILED'),
        (IDLE, 'IDLE'),
        (PARTIAL_FAILURE, 'PARTIAL FAILURE'),
    )
    uniform_resource_locator = models.URLField(max_length=2083, blank=False, null=False)
    upload_date              = models.DateTimeField(auto_now=True)
    status                   = models.IntegerField(choices=STATUS_CHOICES, default=IDLE)
    scan                     = models.ForeignKey(Scan, on_delete=models.CASCADE)

    def get_elapsed_time(self):
        if upload_date:
            # datetime.timedelta object returned
            # Django DateTimeField handles timezone aware datetime objects as well
            time_difference = datetime.datetime.utcnow().replace(tzinfo=utc) - self.upload_date
            return time_difference.total_seconds()

    def __unicode__(self):
        return "{0} @ {1} for {2}".format(self.status, self.uniform_resource_locator, scan.uniform_resource_locator)
