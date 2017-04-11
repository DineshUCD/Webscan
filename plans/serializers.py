from rest_framework import serializers
from plans.models import Plan
from scans.models import Tool, State

class ToolSerializer(serializers.ModelSerializer):
    allow_null=True
    class Meta:
        model  = Tool
        fields = ('module', )

class PlanSerializer(serializers.ModelSerializer):
    tool_set = ToolSerializer(many = True)

    class Meta: 
        model  = Plan
        fields = ('name', 'description', 'tool_set')

    def create(self, validated_data):
        tools_data = validated_data.pop('tool_set')
        request    = self.content.get("request")
        if request and hasattr(request, "user"):
            validated_data["user_profile"] = request.user.userprofile
        plan = Plan.objects.create(**validated_data) 
        for tool_data in tools_data:
            tool, created = Tool.objects.get_or_create(**tool_data) #Just the module information.
            tool.plans.add(plan)
        return plan            
