# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import datetime
import inspect
import json
import os

import pdfkit
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader
from dotenv import load_dotenv

from .reportsLib import ReportCenter

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))


# Create your models here.
class DailyDriveLogParsingStatus(models.Model):
    date = models.DateField()
    buses_count = models.PositiveIntegerField()
    runs_count = models.PositiveIntegerField()
    stoptostop_count = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField()
    exception_bus_count = models.PositiveIntegerField()
    error_code = models.IntegerField()


class ExceptionParsingBus(models.Model):
    date = models.DateField()
    carno = models.CharField(max_length=15)


# class TaskControl:

def get_parsing_result(latest: int = 7):
    return DailyDriveLogParsingStatus.objects.order_by('-date')[:latest]

def add_parsing_result(date: datetime.date,
                       bus_count: int = 0, runs_count: int = 0, stoptostop_count: int = 0,
                       exception_bus_count: int = 0, time_spent: int = 0, error_code: int = 0):
    result = {
        'buses_count': bus_count,
        'runs_count': runs_count,
        'stoptostop_count': stoptostop_count,
        'exception_bus_count': exception_bus_count,
        'error_code': error_code,
        'time_spent': time_spent,
    }
    DailyDriveLogParsingStatus.objects.update_or_create(date=date, defaults=result)


def add_exception_bus(err_bus: list, date: datetime.date):
    for bus in err_bus:
        ExceptionParsingBus.objects.update_or_create(date=date, carno=bus)


def get_report_index_str():
    rc = ReportCenter()
    index_table = []
    for rn in rc.report_list:
        r = rc.create_empty_report(rn)
        index_table.append({"type": rn, "title": r.title, "simple_description": r.simple_description,
                            "args": list(inspect.signature(r.generate_report).parameters)})

    context = {
        'segment': 'report_index',
        'index_table': index_table,
    }
    return context


def parsing_get_report(request, rtype, para_received):
    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)
    report.generate_report(**para_received)

    context = {
        'segment': 'report_index',
        'rtype': rtype,
        'title': report.title,
        'sub_title': report.sub_title,
        'sub_title2': report.sub_title2,
        'start_time': report.start_time,
        'end_time': report.end_time,
        'report': report.parsing_df_for_user().to_html(),
    }

    if "type" in para_received and para_received['type'] == 'pdf':
        load_template = 'app/report_simple.html'
        html_template = loader.get_template(load_template)
        html_string = html_template.render(context, request)
        pdf = pdfkit.from_string(html_string, False)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="{rtype + "_" + report.start_time.strftime("%Y_%m_%d")}.pdf"'
        return response

    else:
        load_template = 'app/report_view.html'
        html_template = loader.get_template(load_template)
        html_string = html_template.render(context, request)
        return HttpResponse(html_string)
