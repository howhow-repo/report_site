# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os, json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django import template
from .models import get_report_index_str, parsing_post_report, parsing_get_report
from .models import add_parsing_result
from .tasks import trigger_stacking
from .reportsLib import ReportCenter, StationCenter
from dotenv import load_dotenv
import inspect

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))


def test_button(request):
    add_parsing_result(date=datetime(1992, 11, 29), bus_count=333, exception_bus_count=3, error_code=0)
    return HttpResponse("ok")


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('app/task_info.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
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
    except:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


# @login_required(login_url="/login/")
def report_index(request):
    context = get_report_index_str()

    if request.method == 'GET':
        load_template = 'app/ui-report_index.html'
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))
    elif request.method == 'POST':
        return HttpResponse(context['index_table'], content_type="application/json")


# @login_required(login_url="/login/")
def report_prehandle(request):
    rtype = request.GET.get('rtype', None)
    if rtype is None:
        return redirect("/report_index/")

    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)
    rtype_paras = list(inspect.signature(report.generate_report).parameters)

    context = {
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
            context['rids'] = get_rid_options(sc)
        if 'vid' in rtype_paras:
            context['vids'] = get_vid_options(sc)
        sc.disconnect()

    load_template = 'app/ui-report_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


# @login_required(login_url="/login/")
def report_view(request, rtype):
    if request.method == 'POST':
        body = json.loads(request.body.decode('utf-8'))
        para_received = body
        para_received = format_paras(para_received)
        return parsing_post_report(request=request, rtype=rtype, para_received=para_received)

    elif request.method == "GET":
        para_received = format_paras(dict(request.GET.items()))
        return parsing_get_report(request=request, rtype=rtype, para_received=para_received)

    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render({}, request))


def trigger_daily_task(request):
    if request.method == 'POST':
        d = {'start_date': None, 'end_date': None}
        body = json.loads(request.body.decode('utf-8'))
        para_received = body
        if (not ('confirm' in para_received)) or (para_received['confirm'] != True):
            return JsonResponse({'comment': 'confirm not True'})

        if 'start_date' in para_received:
            d['start_date'] = datetime.strptime(para_received["start_date"], '%Y-%m-%d')
            if 'end_date' in para_received:
                d['end_date'] = datetime.strptime(para_received["end_date"], '%Y-%m-%d')
        result = trigger_stacking(start_date=d['start_date'], end_date=d['end_date'])
        return JsonResponse(result)
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render({}, request))


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

    return para_received


def get_rid_options(sc: StationCenter) -> list:
    rids = []
    rdf = sc.get_routes_ch_name()
    for i in range(len(rdf['rid'])):
        r = {
            "rid": rdf['rid'].loc[i],
            "name": rdf['name'].loc[i]
        }
        rids.append(r)
    return rids


def get_vid_options(sc: StationCenter) -> list:
    vids = []
    vdf = sc.get_vids_ch_name()
    for i in range(len(vdf['vid'])):
        v = {
            "vid": vdf['vid'].loc[i],
            "name": vdf['name'].loc[i]
        }
        vids.append(v)
    return vids
