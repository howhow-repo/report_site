from django.contrib import admin

# Register your models here.
from data_traffic.models import DailyDataTrafficParsingStatus


class DailyDataTrafficParsingStatusAdmin(admin.ModelAdmin):
    list_display = ('date', 'time_spent', 'status')


admin.site.register(DailyDataTrafficParsingStatus, DailyDataTrafficParsingStatusAdmin)
