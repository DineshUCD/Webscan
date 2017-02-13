from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from scans.models import Tool, Plan, Scan
from urllib2 import urlopen

class ToolSerializer(serializers.ModelSerializer):
    allow_null = True
    class Meta:
        model = Tool
        fields = ('module','name',)

class PlanSerializer(serializers.ModelSerializer):
    tool_set = ToolSerializer(many=True)

    class Meta:
        model = Plan
        fields = ('name', 'description', 'tool_set')
   
    def create(self, validated_data):
        tools_data = validated_data.pop('tool_set')

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['user_profile'] = request.user.userprofile
        
         #Plan object created with name and description.
         #Missing (scan,).
        plan = Plan.objects.create(**validated_data)

        for tool_data in tools_data:
            Tool.objects.create(plan=plan, **tool_data)
    
        return plan

#provide a way of serializing and deserializing the Scan instances 
#into representations such as json
class ScanSerializer(serializers.ModelSerializer):

    class Meta:
        meta = Scan
        fields = ('uniform_resource_locator',)
         
    def validate_uniform_resource_locator(self, value):
        status_code = urlopen(value).code
        if (status_code / 100 >= 4):
            raise serializers.ValidationError("URL " + str(value) + " is not available.")
        return value

    def create(self, validated_data):
        request          = self.context.get("request")
        #Passed from the HTML front-end via an AJAX API call.
        plan_primary_key = int(validated_data.pop("plan_primary_key"))
        validated_data['plan'] = Plan.objects.filter(id=plan_primary_key, user_profile__id=int(request.user.userprofile.id)).first()
        if request and hasattr(request, "user"):
            validated_data['user_profile'] = request.user.userprofile
        scan = Scan.objects.create(**validated_data)
        return scan
