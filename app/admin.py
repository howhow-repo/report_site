# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from .models import DailyDriveLogParsingStatus, ExceptionParsingBus

# Register your models here.
admin.site.register(DailyDriveLogParsingStatus)
admin.site.register(ExceptionParsingBus)