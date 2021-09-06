# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os, json
from datetime import datetime, timedelta

from decouple import config
from dotenv import load_dotenv
import inspect

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django import template
from .models import get_report_index_str, parsing_get_report
from .models import get_parsing_result
from .reportsLib import ReportCenter, StationCenter

import logging
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
    context = CONTEXT
    context['segment'] = 'material'
    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def index(request):
    logger.info(f"Client Access From: {visitor_ip_address(request)}")
    context = CONTEXT
    context['segment'] = 'index'
    results = get_parsing_result()
    context['results'] = [vars(r) for r in results]
    # from core.urls import scheduler
    # jobs = scheduler.get_jobs()
    # context['jobs'] = [{"name": j.name, "next_run_time": str(j.next_run_time), "trigger": str(j.trigger)} for j in jobs]
    html_template = loader.get_template('app/task_info.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = CONTEXT
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
    context = CONTEXT
    context = {**context, **get_report_index_str()}

    if request.method == 'GET':
        load_template = 'app/ui-report_index.html'
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def report_prehandle(request):
    rtype = request.GET.get('rtype', None)
    if rtype is None:
        return redirect("/report_index/")

    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)
    rtype_paras = list(inspect.signature(report.generate_report).parameters)

    context = {
        "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
        'segment': 'report_index',
        "rtype": rtype,
        "title": report.title,
        "rtype_paras": rtype_paras,
        "default_values": {
            "d_start_time": (datetime.today() - timedelta(days=1, hours=3)).strftime("%Y-%m-%d"),
            "d_carno": "117-FX",
        },
    }

    if ('rid' in rtype_paras) or ('vid' in rtype_paras):
        sc = StationCenter(sqlOption=sql_options)
        sc.connect()
        if 'rid' in rtype_paras:
            context['rids'] = get_rid_select_options(sc)
        if 'vid' in rtype_paras:
            context['vids'] = get_vid_select_options(sc)
        sc.disconnect()

    load_template = 'app/ui-report_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def report_view(request, rtype):

    if request.method == "GET":
        para_received = format_paras(dict(request.GET.items()))
        return parsing_get_report(request=request, rtype=rtype, para_received=para_received)

    else:
        context = CONTEXT
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


def format_paras(para_received: dict):
    for para in para_received:
        try:
            if str.isnumeric(para_received[para]):
                para_received[para] = int(para_received[para])
        except Exception:
            continue

    if "start_time" in para_received:
        para_received["start_time"] = datetime.strptime(para_received["start_time"], '%Y-%m-%d')
    if "end_time" in para_received:
        para_received["end_time"] = datetime.strptime(para_received["end_time"], '%Y-%m-%d')

    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received


def get_rid_select_options(sc: StationCenter) -> list:
    rids = []
    rdf = sc.get_routes_ch_name()
    for i in range(len(rdf['rid'])):
        r = {
            "rid": rdf['rid'].loc[i],
            "name": rdf['name'].loc[i]
        }
        rids.append(r)
    return rids


def get_vid_select_options(sc: StationCenter) -> list:
    vids = []
    vdf = sc.get_vids_ch_name()
    for i in range(len(vdf['vid'])):
        v = {
            "vid": vdf['vid'].loc[i],
            "name": vdf['name'].loc[i]
        }
        vids.append(v)
    return vids


def visitor_ip_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip