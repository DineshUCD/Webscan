from __future__ import unicode_literals

from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.models import UserProfile
from webscanner import settings

import datetime, sys, os

# Create your models here.
class Scan(models.Model):
    user_profile             = models.ForeignKey(UserProfile)
    uniform_resource_locator = models.URLField(max_length=2083, blank=False, null=False, help_text="Please use the following format: http(s)://")
    application_id           = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(-1), MaxValueValidator(10)])
    date                     = models.DateTimeField(auto_now_add=True)
    success                  = models.NullBooleanField()

    class Meta:
        unique_together = ['user_profile', 'id']

    def get_scan_data(self):
	return { 'output': map(lambda output: output.report, MetaFile.objects.filter(scan__id=self.id).filter(role=MetaFile.SCAN)), 'zip path': self.zip.name }       

    def __unicode__(self):
        return "{0}".format(self.uniform_resource_locator)

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
        zip_name      = str(datetime.datetime.now().strftime("%Y%M%d%H%M%S%f")) + str(instance).replace('http://','',1)
        zip_meta_data = Zip(scan=instance, name=zip_name)
        zip_meta_data.save()
    
class Tool(models.Model):
    plan           = models.ForeignKey('plans.Plan')
    # Example: "<class 'plugins.w3af.W3af'>"
    module         = models.CharField(max_length=256, default="", blank=True)
    # Example: 'w3af_console'
    name           = models.CharField(max_length=256, default="", blank=True)
    date           = models.DateTimeField(auto_now_add=True)
    state          = models.CharField(max_length=256, default="", blank=True)

    def __unicode__(self):
        return "{0}".format(self.name)

class MetaFile(models.Model):
    DOCUMENTATION = 'D'
    SCAN          = 'S'
    FILE_CHOICES= (
        (DOCUMENTATION, 'Documentation'),
        (SCAN         , 'Scan'         ),
    )
    scan         = models.ForeignKey(Scan, on_delete=models.CASCADE)
    store        = models.ForeignKey(Zip, on_delete=models.CASCADE)
    tool         = models.ForeignKey(Tool, on_delete=models.CASCADE, null=True)
    report       = models.FilePathField(default="", match=".*\.(log|json|ini|xml|yml|zip|w3af|afr)") 
    role         = models.CharField(max_length=1, choices=FILE_CHOICES, default=DOCUMENTATION)
    date         = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def get_filename(self):
        return self.report.split("/")[-1]

    def __unicode__(self):
        return "{0} | {1}".format(self.scan.uniform_resource_locator, self.store.name)

