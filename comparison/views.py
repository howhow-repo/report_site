from django.shortcuts import render
import json, os
import logging
from decouple import config
from dotenv import load_dotenv
from django.http import HttpResponse, HttpResponseServerError
from django.template import loader
from django.contrib.auth.decorators import login_required

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
    context = CONTEXT

    load_template = 'comparison/comparison_index.html'
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def comparison_prehandle(request, rtype):
    context = CONTEXT
    pass