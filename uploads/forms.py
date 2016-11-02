from django import forms
from .models import Upload
from django.utils import html

class ResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        scan_result = kwargs.pop('scans result', None) 
        super(ResultForm, self).__init(*args, **kwargs)
        if scans:
            self.fields['scans result'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=tuple([(item, item) for item in scan_result]))
