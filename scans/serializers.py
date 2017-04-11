from rest_framework import serializers
from scans.models import Tool, Scan, State
from plans.models import Plan
from plans.serializers import PlanSerializer

from urllib2 import urlopen
from copy import deepcopy

#provide a way of serializing and deserializing the Scan instances 
#into representations such as json
class ScanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer
    class Meta:
        model = Scan
        fields = ('uniform_resource_locator', 'plan')

    def validate_plan(self, value):
        request = self.context.get("request")
         # Returns True if the QuerySet contains any results, and False if not.
        plan = Plan.objects.get(pk=value.id, user_profile__id=request.user.userprofile.id)
        plan_copy = None
        if plan:
            plan_copy    = deepcopy(plan)
            plan_copy.id = None
            plan_copy.save()
            plan_copy.tool_set.add(*plan.tool_set.all())
        return plan_copy

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['user_profile'] = request.user.userprofile
        scan = Scan.objects.create(**validated_data)
        #Containers and user defined types are mutable
        validated_data['plan'].scan = scan
        validated_data['plan'].save()

        State.objects.create(scan=scan) # Create overall state for scan. Tool is null.

        #Create State for each Tool in the Scan
        tools = validated_data['plan'].tool_set.all()
        for tool in tools:
            State.objects.create(scan=scan, tool=tool) # Create state for each tool.
                    
        return scan

    def to_representation(self, instance):
        ret = super(ScanSerializer, self).to_representation(instance)
        ret['plan'] = str(instance.plan).lower()
        ret['state'] = State.objects.get(scan=instance, tool=None).get_state()
        ret['date'] = instance.date
        ret['tools'] = list()
        ret['pk'] = instance.id
        for tool in instance.plan.tool_set.all():
            state = State.objects.get(scan=instance, tool=tool)
            tool_information = { tool.name: state.get_state() }
            if state.test != None:
                tool_information['test'] = state.test
            ret['tools'].append(tool_information)
                                   
        return ret
