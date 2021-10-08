import logging

from decouple import config
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponse, HttpResponseNotFound
from django.template import loader
from dotenv import load_dotenv

from .form import ParaInput
from .reportsLib import *

logger = logging.getLogger(__name__)

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    "segment": 'comparison',
}


@login_required(login_url="/login/")
def comparison_index(request):
    context = CONTEXT.copy()
    context['report_list'] = ComparisonReportCenter.list_of_dict()

    load_template = 'comparison/comparison_index.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def comparison_prehandle(request, rtype):
    context = CONTEXT.copy()
    report = ComparisonReportCenter.find_report_type(rtype)
    if report.rtype is None:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))  # return if rtype not in list

    context['rtype'] = rtype
    context['title'] = report.title
    context['paras_comm'] = report.paras_comm
    context['paras_A'] = report.paras_A
    context['paras_B'] = report.paras_B

    context['paras_form'] = ParaInput()

    load_template = 'comparison/comparison_prehandle.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def comparison_result(request, rtype):
    context = CONTEXT.copy()
    context['rtype'] = rtype
    report = ComparisonReportCenter.find_report_type(rtype)()
    if report.rtype is None:
        html_template = loader.get_template('page-404.html')
        return HttpResponseNotFound(html_template.render(context, request))  # return if rtype not in list

    paras_form = ParaInput(request.POST)
    if paras_form.is_valid():
        for f in paras_form.cleaned_data:
            value = paras_form.cleaned_data[f]
            if f in report.paras_A or f in report.paras_comm:
                report.chart_A['paras'].update({f: value})
            if f in report.paras_B or f in report.paras_comm:
                report.chart_B['paras'].update({f: value})

    report.format_paras(report.chart_A)
    report.format_paras(report.chart_B)
    report.calculate_results()

    context['chart_A'] = report.chart_A
    context['chart_B'] = report.chart_B

    context['compare_value'] = report.compare_value
    context['chart_type'] = report.chart_type
    context['hour_range'] = list(range(24))

    context['chartMaxHight'] = max([
        max([r[report.compare_value] for r in report.chart_A['result']]),
        max([r[report.compare_value] for r in report.chart_B['result']]),
    ])

    context['diff'] = (abs(report.result_A[report.compare_value] - report.result_B[report.compare_value]).to_list())
    context['diff_max'] = max(context['diff'])

    load_template = 'comparison/comparison_view.html'
    html_template = loader.get_template(load_template)

    return HttpResponse(html_template.render(context, request))
