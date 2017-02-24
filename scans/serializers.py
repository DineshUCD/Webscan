from rest_framework import serializers
from scans.models import Tool, Scan
from plans.models import Plan
from plans.serializers import PlanSerializer
from webscanner.celery_tasks import app
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

    def validate_plan(self, value):
        request = self.context.get("request")
         # Returns True if the QuerySet contains any results, and False if not.
        if Plan.objects.filter(pk=value.id, user_profile__id=request.user.userprofile.id).exists():
            plan_copy = Plan.objects.create(user_profile=request.user.userprofile, name=value.name, description=value.description)
            for tool in value.tool_set.all():
                Tool.objects.create(plan=plan_copy, module=tool.module, name=tool.name)
            return plan_copy
        else:
            return None

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
        ret = super(ScanSerializer, self).to_representation(instance)
        ret['plan'] = str(instance.plan).lower()
        
        result = app.AsyncResult(str(instance.task_id))
        state  = str(result.state)[:7]
        ret['state'] = state
        Scan.objects.filter(pk=instance.pk).update(state=state)

        ret['tools'] = list()
        for tool in instance.plan.tool_set.all():
            result = app.AsyncResult(str(tool.task_id))
            state = str(result.state)[:7]

            ret['tools'].append({tool.name:state})
            Tool.objects.filter(pk=tool.pk).update(state=state)
               
                     
        return ret
