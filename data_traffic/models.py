from django.db import models
from datetime import datetime


# Create your models here.


class DailyDataTrafficParsingStatus(models.Model):
    date = models.DateField()
    time_spent = models.PositiveIntegerField()
    status = models.BooleanField()


def add_data_traffic_parsing_result(date: datetime.date, time_spent: int = 0, status: bool = True):
    result = {
        'time_spent': time_spent,
        'status': status,
    }
    DailyDataTrafficParsingStatus.objects.update_or_create(date=date, defaults=result)
