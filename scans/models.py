from __future__ import unicode_literals

from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime, sys, os
from webscanner import settings

# Create your models here.
class Scan(models.Model):
    uniform_resource_locator = models.URLField(max_length=2083, blank=False, null=False, help_text="Please use the following format: http(s)://")
    team_id                  = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(-1), MaxValueValidator(10)])
    date                     = models.DateTimeField(auto_now_add=True)
   
    def __unicode__(self):
        return "{0} {1}".format(self.uniform_resource_locator, self.team_id)
"""
Fields: scan, name, uploaded_to,   date
Types: 1 - 1, char, file path char,DateTime 
Usage: Each Scan has one Zip file of config.ini, logs, scan results, and environment variables.
       Name of zip file.
       Absolute path it has been uplaoded to.
       Date it was created.
"""
class Zip(models.Model):
    scan        = models.OneToOneField(Scan, on_delete=models.CASCADE, primary_key=True)
    name        = models.CharField(max_length=256, default="")
    uploaded_to = models.FilePathField(default="")
    date        = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "{0}".format(self.name)

@receiver(post_save, sender=Scan)
def create_zip_for_scan(sender, instance, created, **kwargs):
    if created:
        zip_name      = str(instance.uniform_resource_locator) + " " + str(datetime.datetime.now()) + ".zip"
        zip_meta_data = Zip(scan=instance, name=zip_name)
        zip_meta_data.save()

class MetaFile(models.Model):
    DOCUMENTATION = 'D'
    SCAN          = 'S'
    FILE_CHOICES= (
        (DOCUMENTATION, 'Documentation'),
        (SCAN         , 'Scan'         ),
    )
    scan         = models.ForeignKey(Scan, on_delete=models.CASCADE)
    store        = models.ForeignKey(Zip, on_delete=models.CASCADE)
    report       = models.FilePathField(default="", match=".*\.(log|ini|xml|yml|zip|w3af|afr)") 
    success      = models.BooleanField(default=False)
    role         = models.CharField(max_length=1, choices=FILE_CHOICES, default=DOCUMENTATION)
    date         = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get_filename(self):
        return self.report.split("/")[-1]

    def __unicode__(self):
        return "{0} | {1}".format(self.scan.uniform_resource_locator, self.store.name)