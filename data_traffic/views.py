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
    "segment": 'data_traffic',
}

# Create your views here.
@login_required(login_url="/login/")
def data_traffic_prehandle(request):
    context = CONTEXT
    context["title"] = "資料流 流量統計"
    context["default_values"] = {
                                 "d_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                                 }

    load_template = 'data_traffic/data_traffic_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def data_traffic_view(request):
    context = CONTEXT
    if request.method == "POST":
        para_received = (dict(request.POST))
        date = datetime.strptime(para_received['date'][0], '%Y-%m-%d')
        print(date)

        html_template = loader.get_template('data_traffic/data_traffic_view.html')
        return HttpResponse(html_template.render(context, request))
    else:
        html_template = loader.get_template('page-500.html')
        return HttpResponseServerError(html_template.render(context, request))