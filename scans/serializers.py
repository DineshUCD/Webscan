from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from scans.models import Tool, Plan

class ToolSerializer(serializers.ModelSerializer):
    allow_null = True
    class Meta:
        model = Tool
        fields = ('module',)

class PlanSerializer(serializers.ModelSerializer):
    tool_set = ToolSerializer(many=True)

    class Meta:
        model = Plan
        fields = ('name', 'description', 'tool_set')
   
    def create(self, validated_data):
        tools_data = validated_data.pop('tool_set')

        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['user_profile'] = request.user.userprofile
        
         #Plan object created with name and description.
         #Missing (scan,).
        plan = Plan.objects.create(**validated_data)

        for tool_data in tools_data:
            Tool.objects.create(plan=plan, **tool_data)
    
        return plan
