from django.db import models


class LineNotifyControl(models.Model):
    name = models.CharField(max_length=20)
    token = models.CharField(max_length=50)
    activate = models.BooleanField(default=True)


def add_notify_user(name: str, token: str, activate: bool):
    LineNotifyControl.objects.get_or_create(
        defaults={'name': name, 'token': token, 'activate': activate},
        name=name,
    )
