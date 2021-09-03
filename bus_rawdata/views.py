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
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
}


@login_required(login_url="/login/")
def bus_rawdata_prehandle(request):
    context = {
        "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
        'segment': 'bus_rawdata',
        "title": "公車 原始資料調用",
        "default_values": {
            "d_carno": "117-FX",
            "d_date_begin": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "d_date_end": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
    }

    load_template = 'bus_rawdata/bus_rawdata_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))