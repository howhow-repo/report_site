from datetime import datetime,timedelta

from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class ParaInput(forms.Form):
    date = forms.DateField(
        required=True,
        widget=DateInput,
        initial=lambda: (datetime.today()-timedelta(days=1)),
        label="日期",
    )
