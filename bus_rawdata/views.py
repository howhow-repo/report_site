import json
import logging
import os
from datetime import datetime, timedelta

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.template import loader
from dotenv import load_dotenv

from app.reportsLib import Bus

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'bus_rawdata',
}


@login_required(login_url="/login/")
def bus_rawdata_prehandle(request):
    context = CONTEXT
    context["title"] = "公車 原始資料調用"
    context["default_values"] = {"d_carno": "117-FX",
                                 "d_start_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                                 "d_end_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                                 }

    load_template = 'bus_rawdata/bus_rawdata_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def bus_rawdata_view(request):
    context = CONTEXT
    if request.method == "POST":
        para_received = format_paras(dict(request.POST))
        bus = Bus(MongoDBPath=json.loads(os.getenv("EBUS_MONGODB")), sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        bus.connect()
        bus.carno = para_received['carno']
        bus.setup(start_time=para_received['start_time'], end_time=para_received['end_time'])
        bus.disconnect()

        context['carno'] = para_received['carno']
        context['start_time'] = para_received['start_time']
        context['end_time'] = para_received['end_time']
        context['runs'] = [r.df.to_dict('records')[0] for r in bus.runs]
        for i, r in enumerate(context['runs']):
            r['runs_log'] = bus.runs[i].logs.to_dict('records')

        for l in context['runs']:
            print(l)
        html_template = loader.get_template('bus_rawdata/bus_rawdata_view.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))


def format_paras(para_received: dict):
    logger.debug(f"parameters: {para_received}")
    para_received["carno"] = para_received["carno"][0]
    para_received["start_time"] = datetime.strptime(para_received["start_time"][0], '%Y-%m-%d')
    para_received["end_time"] = datetime.strptime(para_received["end_time"][0], '%Y-%m-%d')
    return para_received
