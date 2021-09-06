from django.contrib import admin
from .models import LineNotifyControl
# Register your models here.


class LineNotifyAdmin(admin.ModelAdmin):
    list_display = ('name', 'token', 'activate')

admin.site.register(LineNotifyControl, LineNotifyAdmin)
