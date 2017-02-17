from django import forms
from django.http import HttpResponse

from .models import Plan
from scans.models import Tool
from scans.tasks import find_all_interfaces

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        self.user_profile_id = kwargs.pop('user_profile_id', None)
        super(PlanForm, self).__init__(*args, **kwargs)

        CHOICES = tuple(find_all_interfaces())
        if all(CHOICES):
            self.fields['plugins'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=CHOICES)
            self.options = dict(CHOICES)

    def clean(self):
        cleaned_data = super(PlanForm, self).clean()

        plugin_choices = cleaned_data.get('plugins')

        Tool.objects.filter(plan__id=self.instance.id).delete()
        
        if not self.instance.user_profile_id:
            self.instance.user_profile_id = self.user_profile_id

        self.instance.save()

        for plugin in plugin_choices:
            Tool.objects.create(plan=self.instance, module=plugin, name=self.options.get(plugin))

        return cleaned_data
