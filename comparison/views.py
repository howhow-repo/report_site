import ast
import json
import logging
import os
from datetime import datetime

from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.template import loader
from dotenv import load_dotenv

from .form import ParaInput

logger = logging.getLogger(__name__)

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'comparison',
}

report_list = [
        {
            'rtype': 'traveltime_weekday',
            'title': '行駛時間與星期比較表',
            'description': '比較不同星期時，站與站之間的行駛時間。',
            'paras_comm': ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end'],
            'paras_A':['weekday_A'],
            'paras_B':['weekday_B']
        },
        {
            'rtype': 'traveltime_weekdayType',
            'title': '行駛時間與日種類比較表',
            'description': '比較不同種日時，站與站之間的行駛時間。',
            'paras_comm': ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end'],
            'paras_A':['weekdayType_A'],
            'paras_B':['weekdayType_B']
        },
        {
            'rtype': 'stayltime_weekday',
            'title': '站內停留時間與星期比較表',
            'description': '比較不同星期時，站內停留時間。',
            'paras_comm': ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end'],
            'paras_A':['weekday_A'],
            'paras_B':['weekday_B']
        },
        {
            'rtype': 'stayltime_weekdayType',
            'title': '站內停留時間與日種類比較表',
            'description': '比較不同種日時，站內停留時間。',
            'paras_comm': ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end'],
            'paras_A':['weekdayType_A'],
            'paras_B':['weekdayType_B']
        },
    ]


@login_required(login_url="/login/")
def comparison_index(request):
    context = CONTEXT.copy()
    context['report_list'] = report_list.copy()

    load_template = 'comparison/comparison_index.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def comparison_prehandle(request, rtype):
    context = CONTEXT.copy()
    context['rtype'] = rtype
    if rtype not in [r['rtype'] for r in report_list ]:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request)) # return if rtype not in list

    for r in report_list:
        if r['rtype'] == rtype:
            context['title'] = r['title']
            context['rtype_paras_comm'] = r['paras_comm']
            context['rtype_paras_A'] = r['paras_A']
            context['rtype_paras_B'] = r['paras_B']
            break

    context['para_form'] = ParaInput()

    load_template = 'comparison/comparison_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def comparison_result(request, rtype):
    r = (dict(request.POST))
    charA_paras = {
        "rid": (ast.literal_eval(r['rid_stat'][0]))[0],
        "rid_name": (ast.literal_eval(r['rid_stat'][0]))[1],
        "date_begin": datetime.strptime(r['date_begin'][0],'%Y-%m-%d'),
        "date_end": datetime.strptime(r['date_end'][0], '%Y-%m-%d'),
        "hour_begin": int(r['hour_begin'][0]),
        "hour_end": int(r['hour_end'][0]),
    }

    charB_paras = {
        "rid": (ast.literal_eval(r['rid_stat'][1]))[0],
        "rid_name": (ast.literal_eval(r['rid_stat'][1]))[1],
        "date_begin": datetime.strptime(r['date_begin'][1], '%Y-%m-%d'),
        "date_end": datetime.strptime(r['date_end'][1], '%Y-%m-%d'),
        "hour_begin": int(r['hour_begin'][1]),
        "hour_end": int(r['hour_end'][1]),
    }

    return JsonResponse([charA_paras, charB_paras], safe=False)