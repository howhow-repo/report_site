import json
import logging
import os
from datetime import datetime, timedelta

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.template import loader
from dotenv import load_dotenv

from app.reportsLib import StationCenter, StopToStopResult

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
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
    context = {
        "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
        'segment': 'stoptostop',
        "title": "站到站 資訊統計",
        "default_values": {
            "d_date_begin": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "d_date_end": (datetime.now()).strftime("%Y-%m-%d"),
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
        para_received = format_stoptostop_paras(dict(request.POST))
        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        sr.connect()
        rp = (sr.get_default_stop_to_stop_by_rid(**para_received))
        context['chartMaxHight'] = max(rp['avg_arrival_time_spent'].tolist())

        rp.fillna("", inplace=True)
        context['result'] = rp.to_dict('records')
        sr.disconnect()

        context['rid'] = para_received['rid']
        context['rid_name'] = para_received['rid_name']
        context['date_begin'] = para_received['date_begin']
        context['date_end'] = para_received['date_end']
        context['hour_begin'] = para_received['hour_begin']
        context['hour_end'] = para_received['hour_end']
        context['weekdayType'] = para_received['weekdayType']
        context['weekdayType_cn'] = para_received['weekdayType_cn']

        html_template = loader.get_template('stoptostop_analysis/stoptostop_result.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


@login_required(login_url="/login/")
def stoptostop_hourly(request, rsid):
    context = CONTEXT
    if request.method == "POST":
        para_received = format_hourly_paras(dict(request.POST))
        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        sr.connect()
        rp = (sr.get_stop_to_stop_hourly_by_rsid(rsid=rsid, **para_received))
        rp.fillna(0, inplace=True)
        context['chartMaxHight'] = max(rp['avg_arrival_time_spent'].tolist())
        context['result'] = rp.to_dict('records')
        sr.disconnect()

        context['rsid'] = rsid
        context['rsid_name'] = para_received['rsid_name']
        context['pre_rsid_name'] = para_received['pre_rsid_name']
        context['rid'] = para_received['rid']
        context['rid_name'] = para_received['rid_name']
        context['date_begin'] = para_received['date_begin']
        context['date_end'] = para_received['date_end']
        context['weekdayType'] = para_received['weekdayType']
        context['weekdayType_cn'] = para_received['weekdayType_cn']

        html_template = loader.get_template('stoptostop_analysis/stoptostop_hourly.html')
        return HttpResponse(html_template.render(context, request))

    else:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))


weekdayType_cn = {
    "0": "平日",
    "1": "週末",
    "2": "國定假日",
    "3": "彈性放假",
    "4": "補假",
    "5": "補班",
    "6": "特殊假日",
}


def format_stoptostop_paras(para_received: dict):
    stat = dict(json.loads(para_received["rid_stat"][0]))
    para_received["rid"] = int(stat['rid_stat'][0])
    para_received["rid_name"] = stat['rid_stat'][1]
    para_received["weekdayType_cn"] = [weekdayType_cn[w] for w in para_received["weekdayType"]]
    para_received["weekdayType"] = [int(w) for w in para_received["weekdayType"]]
    para_received["date_begin"] = datetime.strptime(para_received["date_begin"][0], '%Y-%m-%d')
    para_received["date_end"] = datetime.strptime(para_received["date_end"][0], '%Y-%m-%d')
    para_received["hour_begin"] = int(para_received["hour_begin"][0])
    para_received["hour_end"] = int(para_received["hour_end"][0])
    del para_received['rid_stat']
    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received


def format_hourly_paras(para_received: dict):
    para_received['pre_rsid_name'] = para_received['pre_rsid_name'][0]
    para_received['rid'] = para_received['rid'][0]
    para_received['rid_name'] = para_received['rid_name'][0]
    para_received['rsid_name'] = para_received['rsid_name'][0]
    para_received["weekdayType_cn"] = [weekdayType_cn[str(w)] for w in eval(para_received["weekdayType"][0])]
    para_received["weekdayType"] = [int(w) for w in eval(para_received["weekdayType"][0])]
    para_received["date_begin"] = datetime.strptime(para_received["date_begin"][0], '%Y-%m-%d')
    para_received["date_end"] = datetime.strptime(para_received["date_end"][0], '%Y-%m-%d')
    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received
