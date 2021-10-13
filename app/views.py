# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import inspect
import json
import logging
import os
from datetime import datetime

from decouple import config
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import redirect
from django.template import loader
from dotenv import load_dotenv

from authentication.views import authcheck
from data_traffic.models import get_data_traffic_parsing_result
from .form import ParaInput
from .models import get_parsing_result
from .models import get_report_index_str, parsing_get_report
from .reportsLib import ReportCenter

logger = logging.getLogger(__name__)

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
}


def test_button(request):
    from core.urls import scheduler
    return HttpResponse(scheduler.get_jobs())


def pause_jobs(request):
    from core.urls import scheduler
    scheduler.get_job('runsAndStopStacking').pause()
    return HttpResponse(scheduler.get_jobs())


def resume_jobs(request):
    from core.urls import scheduler
    scheduler.get_job('runsAndStopStacking').resume()
    return HttpResponse(scheduler.get_jobs())


def demo(request):
    context = CONTEXT.copy()
    context['segment'] = 'material'
    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))


def index(request):
    re = authcheck(request)
    if re is not None:
        return re

    logger.info(f"Client Access From: {visitor_ip_address(request)}")
    context = CONTEXT.copy()
    context['segment'] = 'index'

    results = get_parsing_result()
    data_traffic_results = get_data_traffic_parsing_result()

    context['results'] = [vars(r) for r in results]
    context['data_traffic_results'] = [vars(r) for r in data_traffic_results]
    html_template = loader.get_template('app/task_info.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = CONTEXT.copy()
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]
        context['segment'] = load_template
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))

    except Exception as e:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def report_index(request):
    context = CONTEXT.copy()
    context = {**context, **get_report_index_str()}

    if request.method == 'GET':
        load_template = 'app/report_index.html'
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def report_prehandle(request):
    context = CONTEXT.copy()
    rtype = request.GET.get('rtype', None)
    if rtype is None:
        return redirect("/report_index/")

    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)
    rtype_paras = list(inspect.signature(report.generate_report).parameters)

    context.update({
        "segment": "report_index",
        "rtype": rtype,
        "title": report.title,
        "rtype_paras": rtype_paras,
        "para_form": ParaInput()
    })
    load_template = 'app/report_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def report_view(request, rtype):
    if request.method == "GET":
        para_received = format_paras(dict(request.GET.items()))
        return parsing_get_report(request=request, rtype=rtype, para_received=para_received)

    else:
        context = CONTEXT.copy()
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


def format_paras(para_received: dict):
    for para in para_received:
        try:
            if str.isnumeric(para_received[para]):
                para_received[para] = int(para_received[para])
        except Exception:
            continue
    if "carno" in para_received:
        para_received["carno"] = (para_received["carno"].lstrip()).rstrip()
    if "start_time" in para_received:
        para_received["start_time"] = datetime.strptime(para_received["start_time"], '%Y-%m-%d')
    if "end_time" in para_received:
        para_received["end_time"] = datetime.strptime(para_received["end_time"], '%Y-%m-%d')

    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received


def visitor_ip_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
