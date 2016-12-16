from django import forms
from .models import Upload
from django.utils import html

class ResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        scan_results = kwargs.pop('scan_results', None) 
        super(ResultForm, self).__init__(*args, **kwargs)
        if scan_results:
            self.fields['scan_results'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=tuple([(item, item) for item in scan_results]))
