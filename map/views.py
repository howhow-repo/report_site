# -*- encoding: utf-8 -*-
import json
import os

from django.http import HttpResponse
from django.shortcuts import render, redirect
from decouple import config
from django.template import loader

# Create your views here.
from django.urls import reverse

from app.reportsLib import StationCenter
from map.form import ParaInput

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    'segment': 'map',
    'title': '地圖(測試)',
}


def map_prehandle(request):
    context = CONTEXT.copy()
    context["para_form"] = ParaInput()
    html_template = loader.get_template('map/map_prehandle.html')
    return HttpResponse(html_template.render(context, request))


def map_rid(request):
    context = CONTEXT.copy()
    if 'rid' not in dict(request.GET.items()):
        return redirect(reverse('map_prehandle'))
    rid = int(dict(request.GET.items())['rid'])
    station = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    station.connect()
    stop_locations = [[s['clon'], s['clat']] for s in station.get_route_stop_location(rid=rid).to_dict('records')]
    station.disconnect()
    # geojson_points = {
    #                      "type": "MultiPoint",
    #                      "coordinates": stop_locations,
    #                  },

    geojson_line = {
                       "type": "LineString",
                       "coordinates": stop_locations,
                   },

    geojson_circle = stop_locations

    # context['geojson_points'] = str(json.dumps(geojson_points))
    context['geojson_line'] = str(json.dumps(geojson_line))
    context['geojson_circle'] = geojson_circle

    html_template = loader.get_template('map/map_rid.html')
    return HttpResponse(html_template.render(context, request))
