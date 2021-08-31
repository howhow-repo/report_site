import inspect
import json, os

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from datetime import datetime, timedelta

# Create your views here.
from dotenv import load_dotenv

from app.reportsLib import ReportCenter, StationCenter
import logging

from app.views import get_rid_select_options

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
}


@login_required(login_url="/login/")
def stoptostop_prehandle(request):
    context = {
        "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
        'segment': 'stoptostop',
        "title": "站到站 資訊統計",
        "default_values": {
            "d_date_begin": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "d_date_end": (datetime.now()).strftime("%Y-%m-%d"),
            "d_hour_begin": "00:00:00",
            "d_hour_end": "23:59:00",
        },
    }

    sc = StationCenter(sqlOption=sql_options)
    sc.connect()
    context['rids'] = get_rid_select_options(sc)
    sc.disconnect()

    load_template = 'stoptostop_analysis/stoptostop_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))
