# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from .models import DailyDriveLogParsingStatus, ExceptionParsingBus


# Register your models here.
class DailyDriveLogParsingAdmin(admin.ModelAdmin):
    list_display = ('date', 'buses_count', 'runs_count', 'time_spent', 'exception_bus_count', 'error_code')


class ExceptionParsingBusAdmin(admin.ModelAdmin):
    list_display = ('date', 'carno')


admin.site.register(DailyDriveLogParsingStatus, DailyDriveLogParsingAdmin)
admin.site.register(ExceptionParsingBus, ExceptionParsingBusAdmin)
