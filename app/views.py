# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os, json
from datetime import datetime, timedelta

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django import template

from .reportsLib import ReportCenter
from dotenv import load_dotenv
import inspect

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))


@login_required(login_url="/login/")
def index(request):
    context = {}
    context['segment'] = 'index'

    html_template = loader.get_template('index.html')
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
    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)

    context = {
        'list': rc.simple_description,
    }
    load_template = 'app/ui-report_index.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def report_prehandle(request):
    rtype = request.GET.get('rtype', None)
    if rtype is None:
        return redirect("/report_index/")

    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)

    context = {
        "rtype": rtype,
        "title": report.title,
        "default_values": {
            "d_start_time": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "d_rid": 6,
            "d_carno": "117-FX",
            "d_vid": 29
        },
    }
    load_template = 'app/ui-report_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


# @login_required(login_url="/login/")
def report_view(request, rtype, para_received=None):
    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)

    if request.method == 'POST':
        body = json.loads(request.body.decode('utf-8'))
        para_received = body
        para_received = format_paras(para_received)

        report.generate_report(**para_received)
        return HttpResponse(report.report.to_json(), content_type="application/json")


    elif request.method == "GET":
        para_received = format_paras(dict(request.GET.items()))
        print(para_received)
        report.generate_report(**para_received)

        s = datetime.strftime(report.start_time, '%Y-%m-%d')
        e = datetime.strftime(report.end_time, '%Y-%m-%d')
        context = {
            'title': report.title,
            'sub_title': 'sub_title',
            'time_range': f'{s}~{e}',
            'report': report.parsing_df_for_user().to_html(),
        }
        load_template = 'app/report_base_view.html'
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))

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
