# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os, json
from datetime import datetime, timedelta

import pdfkit
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django import template

from .reportsLib import ReportCenter, StationCenter
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


@login_required(login_url="/login/")
def report_index(request):
    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)

    index_table = []
    for rn in rc.report_list:
        r = rc.create_empty_report(rn)
        index_table.append({'type': rn, 'title': r.title, 'simple_description': r.simple_description})

    context = {
        'index_table': index_table,
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
    rtype_paras = list(inspect.signature(report.generate_report).parameters)

    context = {
        "rtype": rtype,
        "title": report.title,
        "rids": [{}],
        "vids": [{}],
        "rtype_paras": rtype_paras,
        "default_values": {
            "d_start_time": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "d_rid": 6,
            "d_carno": "117-FX",
            "d_vid": 29
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
        report.generate_report(**para_received)

        context = {
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

    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render({}, request))


def html2pdf(request):
    if request.method == 'POST':
        html_string = request.body.decode('utf-8')
        print(html_string)
        pdf = pdfkit.from_string(html_string, False)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment;filename="{"1234"}.pdf"'
        return response
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
