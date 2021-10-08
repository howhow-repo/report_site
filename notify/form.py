from datetime import datetime, timedelta
from django import forms


class AddNotify(forms.Form):
    name = forms.CharField(required=True)
    name.label = "名稱"

    token = forms.CharField(required=True)
    token.label = "權杖(token)"

    activate = forms.BooleanField(required=False, initial=True)
    activate.label = "啟用"
