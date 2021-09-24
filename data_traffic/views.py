import json
import logging
import os
from datetime import datetime, timedelta

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.template import loader
from dotenv import load_dotenv

from app.reportsLib import Bus, StationCenter
from .form import ParaForm

logger = logging.getLogger('django')

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'data_traffic',
}

# Create your views here.
@login_required(login_url="/login/")
def data_traffic_prehandle(request):
    context = CONTEXT
    context["title"] = "資料流 流量統計"
    context["para_form"] = ParaForm()

    load_template = 'data_traffic/data_traffic_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def data_traffic_view(request):
    context = CONTEXT
    if request.method == "POST":
        para_received = (dict(request.POST))
        date = datetime.strptime(para_received['date'], '%Y-%m-%d')

        sc = StationCenter(sqlOption=sql_options)
        sc.connect()
        df = sc.get_data_traffic(date)
        sc.disconnect()

        context['hour'] = list(range(0,24))
        context['date'] = date
        context['gps_data_count_max'] = max(df['gps_data_count'])
        context['drivelog_data_count_max'] = max(df['drivelog_data_count'])
        context['bus_on_rail_count_max'] = max(df['bus_on_rail_count'])
        context['bus_online_count_max'] = max(df['bus_online_count'])
        context['report'] = df.to_dict('records')

        html_template = loader.get_template('data_traffic/data_traffic_view.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))