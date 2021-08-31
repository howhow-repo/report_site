import inspect
import json, os

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render, redirect
from django.template import loader
from datetime import datetime, timedelta

# Create your views here.
from dotenv import load_dotenv

from app.reportsLib import ReportCenter, StationCenter, StopToStopResult
import logging

from app.views import get_rid_select_options

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))

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


@login_required(login_url="/login/")
def stoptostop_view(request):
    context = CONTEXT
    if request.method == "POST":
        para_received = format_paras(dict(request.POST))
        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        sr.connect()
        context['result'] = sr.get_default_stop_to_stop_by_rid(**para_received).to_dict('records')
        sr.disconnect()

        context['rid'] = para_received['rid']
        context['date_begin'] = para_received['date_begin']
        context['date_end'] = para_received['date_end']
        context['hour_begin'] = para_received['hour_begin']
        context['hour_end'] = para_received['hour_end']
        context['weekdayType'] = para_received['weekdayType']

        html_template = loader.get_template('stoptostop_analysis/stoptostop_result.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


def format_paras(para_received: dict):
    para_received["rid"] = int(para_received["rid"][0])
    para_received["weekdayType"] = tuple([int(w) for w in para_received["weekdayType"]])
    para_received["date_begin"] = datetime.strptime(para_received["date_begin"][0], '%Y-%m-%d')
    para_received["date_end"] = datetime.strptime(para_received["date_end"][0], '%Y-%m-%d')
    para_received["hour_begin"] = int(para_received["hour_begin"][0])
    para_received["hour_end"] = int(para_received["hour_end"][0])
    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received