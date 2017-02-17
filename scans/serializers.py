from rest_framework import serializers
from scans.models import Tool, Scan
from plans.serializers import PlanSerializer
from urllib2 import urlopen


#provide a way of serializing and deserializing the Scan instances 
#into representations such as json
class ScanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer
    class Meta:
        model = Scan
        fields = ('uniform_resource_locator', 'plan')
         
    def validate_uniform_resource_locator(self, value):
        status_code = urlopen(value).code
        if (status_code / 100 >= 4):
            raise serializers.ValidationError("URL " + str(value) + " is not available.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['user_profile'] = request.user.userprofile
        scan = Scan.objects.create(**validated_data)

        #Containers and user defined types are mutable
        validated_data['plan'].scan = scan
        validated_data['plan'].save()
        
        return scan

    def to_representation(self, instance):
        ret = super(ScanSerializer, self).to_representation(instancE)
        ret['plan'] = str(instance.plan).lower()
        return ret
