from datetime import datetime, timedelta
from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class ParaInput(forms.Form):
    carno = forms.CharField(required=True, initial="117-FX")
    carno.label = "車號"

    start_time = forms.DateField(required=True, widget=DateInput, initial=datetime.today()-timedelta(days=1))
    start_time.label = "統計起始日"

    end_time = forms.DateField(required=True, widget=DateInput, initial=datetime.today()-timedelta(days=1))
    end_time.label = "統計截止日"
