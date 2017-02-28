from rest_framework import serializers
from scans.models import Scan
from scans.serializers import ScanSerializer
from uploads.models import Upload

class UploadSerializer(serializers.ModelSerializer):
    scan = ScanSerializer
    class Meta:
        model = Upload
        fields = ('uniform_resource_locator', 'application_id', 'scan')
