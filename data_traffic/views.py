import json
import logging
import os
from datetime import datetime, timedelta

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.template import loader
from dotenv import load_dotenv

from app.reportsLib import StationCenter
from .form import ParaInput

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'data_traffic',
}


@login_required(login_url="/login/")
def data_traffic_prehandle(request):
    context = CONTEXT.copy()
    context["title"] = "資料流 流量統計"
    context["para_form"] = ParaInput()

    load_template = 'data_traffic/data_traffic_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def data_traffic_view(request):
    context = CONTEXT.copy()
    if request.method == "POST":
        form = ParaInput(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
        else:
            date = datetime.today()-timedelta(days=1)
            logger.warning("Cannot handle form request.")
        sc = StationCenter(sqlOption=sql_options)
        sc.connect()
        df = sc.get_data_traffic(date)
        sc.disconnect()

        context.update(
            {
                'hour': list(range(0, 24)),
                'date': date,
            }
        )
        if df.empty:
            context.update(
                {
                    'gps_data_count_max': 20000,
                    'drivelog_data_count_max': 5000,
                    'bus_on_rail_count_max': 150,
                    'bus_online_count_max': 150,
                    'err_msg': '無法搜尋到本日紀錄。',
                }
            )

        else:
            context.update(
                {
                    'gps_data_count_max': max(df['gps_data_count']),
                    'drivelog_data_count_max': max(df['drivelog_data_count']),
                    'bus_on_rail_count_max': max(df['bus_on_rail_count']),
                    'bus_online_count_max': max(df['bus_online_count']),
                    'report': df.to_dict('records')
                }
            )

        html_template = loader.get_template('data_traffic/data_traffic_view.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))