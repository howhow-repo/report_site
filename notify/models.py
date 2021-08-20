from django.db import models

# Create your models here.

class LineNotifyControl(models.Model):
    name = models.CharField(max_length=20)
    token = models.CharField(max_length=50)
    activate = models.BooleanField(default=True)