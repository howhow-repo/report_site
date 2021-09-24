from datetime import datetime,timedelta

from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class ParaForm(forms.Form):
    date = forms.DateField(required=True, widget=DateInput, initial=datetime.today()-timedelta(days=1))
    date.label = "日期"
