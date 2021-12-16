import json
import logging
import ast
from datetime import datetime
from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.template import loader

from app.reportsLib import StationCenter, StopToStopResult
from .form import ParaInput

logger = logging.getLogger('django')

sql_options = json.loads(config("EBUS_SQLDB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'stoptostop',
    "title": "站到站 資訊統計",
}


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


@login_required(login_url="/login/")
def stoptostop_prehandle(request):
    context = CONTEXT.copy()
    context["para_form"] = ParaInput()

    load_template = 'stoptostop_analysis/stoptostop_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def stoptostop_traveltime_view(request):
    context = CONTEXT.copy()
    p = ParaInput(request.POST)
    if p.is_valid():
        para_received = format_stoptostop_paras(p)
        sr = StopToStopResult(sqlOption=sql_options)
        sr.connect()
        rp = (sr.get_default_stop_to_stop_by_rid(**para_received))
        context['chartMaxHight'] = max(rp['avg_arrival_time_spent'].tolist())

        rp.fillna("", inplace=True)
        context['result'] = rp.to_dict('records')
        sr.disconnect()

        context.update(
            {
                'rid':  para_received['rid'],
                'rid_name': para_received['rid_name'],
                'date_begin': para_received['date_begin'],
                'date_end': para_received['date_end'],
                'hour_begin': para_received['hour_begin'],
                'hour_end': para_received['hour_end'],
                'weekdayType': para_received['weekdayType'],
                'weekdayType_cn': para_received['weekdayType_cn'],
            }
        )

        html_template = loader.get_template('stoptostop_analysis/stoptostop_traveltime_result.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def stoptostop_staytime_view(request):
    context = CONTEXT.copy()
    p = ParaInput(request.POST)
    if p.is_valid():
        para_received = format_stoptostop_paras(p)
        sr = StopToStopResult(sqlOption=sql_options)
        sr.connect()
        rp = (sr.get_default_stop_to_stop_by_rid(**para_received))
        context['chartMaxHight'] = max(rp['avg_stay_time'].tolist())

        rp.fillna("", inplace=True)
        context['result'] = rp.to_dict('records')
        sr.disconnect()

        context.update(
            {
                'rid': para_received['rid'],
                'rid_name': para_received['rid_name'],
                'date_begin': para_received['date_begin'],
                'date_end': para_received['date_end'],
                'hour_begin': para_received['hour_begin'],
                'hour_end': para_received['hour_end'],
                'weekdayType': para_received['weekdayType'],
                'weekdayType_cn': para_received['weekdayType_cn'],
            }
        )

        html_template = loader.get_template('stoptostop_analysis/stoptostop_staytime_result.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def stoptostop_traveltime_hourly(request, rsid):
    context = CONTEXT.copy()
    if request.method == "POST":
        para_received = format_hourly_paras(dict(request.POST))
        sr = StopToStopResult(sqlOption=sql_options)
        sr.connect()
        rp = (sr.get_stop_to_stop_hourly_by_rsid(rsid=rsid, **para_received))
        sr.disconnect()
        rp.fillna(0, inplace=True)

        context.update(
            {
                'chartMaxHight': max(rp['avg_arrival_time_spent'].tolist()),
                'result': rp.to_dict('records'),
                'rsid': rsid,
                'rsid_name': para_received['rsid_name'],
                'pre_rsid_name': para_received['pre_rsid_name'],
                'rid': para_received['rid'],
                'rid_name': para_received['rid_name'],
                'date_begin': para_received['date_begin'],
                'date_end': para_received['date_end'],
                'weekdayType': para_received['weekdayType'],
                'weekdayType_cn': para_received['weekdayType_cn'],
            }
        )

        html_template = loader.get_template('stoptostop_analysis/stoptostop_traveltime_hourly.html')
        return HttpResponse(html_template.render(context, request))

    else:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))


@login_required(login_url="/login/")
def stoptostop_staytime_hourly(request, rsid):
    context = CONTEXT.copy()
    if request.method == "POST":
        para_received = format_hourly_paras(dict(request.POST))
        sr = StopToStopResult(sqlOption=sql_options)
        sr.connect()
        rp = (sr.get_stop_to_stop_hourly_by_rsid(rsid=rsid, **para_received))
        sr.disconnect()

        rp.fillna(0, inplace=True)

        context.update(
            {
                'chartMaxHight': max(rp['avg_arrival_time_spent'].tolist()),
                'result': rp.to_dict('records'),
                'rsid': rsid,
                'rsid_name': para_received['rsid_name'],
                'rid': para_received['rid'],
                'rid_name': para_received['rid_name'],
                'date_begin': para_received['date_begin'],
                'date_end': para_received['date_end'],
                'weekdayType': para_received['weekdayType'],
                'weekdayType_cn': para_received['weekdayType_cn'],
            }
        )

        html_template = loader.get_template('stoptostop_analysis/stoptostop_staytime_hourly.html')
        return HttpResponse(html_template.render(context, request))

    else:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))


weekdayType_cn = {
    0: "平日",
    1: "週末",
    2: "國定假日",
    3: "彈性放假",
    4: "補假",
    5: "補班",
    6: "特殊假日",
}


def format_stoptostop_paras(p: ParaInput):
    para_received = {}
    stat = ast.literal_eval(p.cleaned_data["rid_stat"])
    para_received["rid"] = int(stat[0])
    para_received["rid_name"] = stat[1]
    para_received["weekdayType_cn"] = [weekdayType_cn[w] for w in p.cleaned_data["weekdayType"]]
    para_received["weekdayType"] = p.cleaned_data["weekdayType"]
    para_received["date_begin"] = p.cleaned_data["date_begin"]
    para_received["date_end"] = p.cleaned_data["date_end"]
    para_received["hour_begin"] = p.cleaned_data["hour_begin"]
    para_received["hour_end"] = p.cleaned_data["hour_end"]
    return para_received


def format_hourly_paras(para_received: dict):
    if "pre_rsid_name" in para_received:
        para_received['pre_rsid_name'] = para_received['pre_rsid_name'][0]
    para_received['rid'] = para_received['rid'][0]
    para_received['rid_name'] = para_received['rid_name'][0]
    para_received['rsid_name'] = para_received['rsid_name'][0]
    para_received["weekdayType_cn"] = [weekdayType_cn[int(w)] for w in eval(para_received["weekdayType"][0])]
    para_received["weekdayType"] = [int(w) for w in eval(para_received["weekdayType"][0])]
    para_received["date_begin"] = datetime.strptime(para_received["date_begin"][0], '%Y-%m-%d')
    para_received["date_end"] = datetime.strptime(para_received["date_end"][0], '%Y-%m-%d')
    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received
