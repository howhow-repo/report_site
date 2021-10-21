# -*- encoding: utf-8 -*-
import json

from django.http import HttpResponse
from django.shortcuts import render
from decouple import config
from django.template import loader

# Create your views here.

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    'segment': 'map',
    'title': '地圖(測試)',
}


def map_index(request):
    context = CONTEXT.copy()
    geojson_sample = {
        "type": "Point",
        "coordinates": [-1.4058208465576172, 47.15301133231325],
    },
    context['geojson_sample'] = str(json.dumps(geojson_sample))
    print(context['geojson_sample'])
    html_template = loader.get_template('map/map_demo.html')
    return HttpResponse(html_template.render(context, request))
