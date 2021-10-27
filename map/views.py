# -*- encoding: utf-8 -*-
import json
import os
import pandas as pd

from django.http import HttpResponse
from django.shortcuts import render, redirect
from decouple import config
from django.template import loader

# Create your views here.
from django.urls import reverse

from app.reportsLib import StationCenter, StopToStopResult
from map.form import ParaInput

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    'segment': 'map',
    'title': '地圖(測試)',
}

weekdayType_cn = {
    0: "平日",
    1: "週末",
    2: "國定假日",
    3: "彈性放假",
    4: "補假",
    5: "補班",
    6: "特殊假日",
}

TIMERANGE = {
    'morning': {
        'b': 5,
        'e': 9,
    },
    'noon': {
        'b': 9,
        'e': 12,
    },
    'afternoon': {
        'b': 12,
        'e': 16,
    },
    'evening': {
        'b': 16,
        'e': 18,
    },
    'night': {
        'b': 18,
        'e': 20,
    },
    'latenight': {
        'b': 20,
        'e': 23,
    },

}


def map_prehandle(request):
    context = CONTEXT.copy()
    context["para_form"] = ParaInput()
    html_template = loader.get_template('map/map_prehandle.html')
    return HttpResponse(html_template.render(context, request))


def map_rid(request):
    context = CONTEXT.copy()
    p = ParaInput(request.POST)
    if not p.is_valid():
        return redirect(reverse('map_prehandle'))

    rid = p.cleaned_data["rid"]

    station = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    station.connect()
    stop_locations_df = station.get_route_stop_location(rid=rid)
    route_ch_name = station.get_route_ch_name(rid=rid)
    line_geostr = decode_googlegeostr(station.get_route_geostr(rid))
    station.disconnect()

    geojson_line = {"type": "LineString", "coordinates": line_geostr}

    para_received = format_stoptostop_paras(p)
    sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    sr.connect()
    rp_morning = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                        'hour_begin': TIMERANGE['morning']['b'],
                                                        'hour_end': TIMERANGE['morning']['e']}))
    rp_noon = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                     'hour_begin': TIMERANGE['noon']['b'],
                                                     'hour_end': TIMERANGE['noon']['e']}))
    rp_afternoon = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                          'hour_begin': TIMERANGE['afternoon']['b'],
                                                          'hour_end': TIMERANGE['afternoon']['e']}))
    rp_evening = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                        'hour_begin': TIMERANGE['evening']['b'],
                                                        'hour_end': TIMERANGE['evening']['e']}))
    rp_night = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                      'hour_begin': TIMERANGE['night']['b'],
                                                      'hour_end': TIMERANGE['night']['e']}))
    rp_latenight = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                          'hour_begin': TIMERANGE['latenight']['b'],
                                                          'hour_end': TIMERANGE['latenight']['e']}))
    sr.disconnect()

    geojson_morning = merge_df_to_dict(stop_locations_df, rp_morning)
    geojson_noon = merge_df_to_dict(stop_locations_df, rp_noon)
    geojson_afternoon = merge_df_to_dict(stop_locations_df, rp_afternoon)
    geojson_evening = merge_df_to_dict(stop_locations_df, rp_evening)
    geojson_night = merge_df_to_dict(stop_locations_df, rp_night)
    geojson_latenight = merge_df_to_dict(stop_locations_df, rp_latenight)

    context['geojson_line'] = str(json.dumps(geojson_line))
    context['stop_location'] = stop_locations_df.to_dict('records')
    context['geojson_morning'] = geojson_morning
    context['geojson_noon'] = geojson_noon
    context['geojson_afternoon'] = geojson_afternoon
    context['geojson_evening'] = geojson_evening
    context['geojson_night'] = geojson_night
    context['geojson_latenight'] = geojson_latenight
    context['route_ch_name'] = route_ch_name
    context['avg_lon'] = sum(stop_locations_df['lon'].tolist()) / len(stop_locations_df['lon'].tolist())
    context['avg_lat'] = sum(stop_locations_df['lat'].tolist()) / len(stop_locations_df['lat'].tolist())
    context['rid'] = p.cleaned_data['rid']
    context['date_begin'] = p.cleaned_data['date_begin']
    context['date_end'] = p.cleaned_data['date_end']
    context['weekdayType'] = p.cleaned_data['weekdayType']
    context['weekdayType_cn'] = [weekdayType_cn[w] for w in p.cleaned_data['weekdayType']]
    context['TIMERANGE'] = TIMERANGE

    html_template = loader.get_template('map/map_rid.html')
    return HttpResponse(html_template.render(context, request))


def format_stoptostop_paras(p: ParaInput):
    para_received = {
        "rid": p.cleaned_data["rid"],
        "weekdayType_cn": [weekdayType_cn[w] for w in p.cleaned_data["weekdayType"]],
        "weekdayType": p.cleaned_data["weekdayType"],
        "date_begin": p.cleaned_data["date_begin"],
        "date_end": p.cleaned_data["date_end"],
    }
    return para_received


def merge_df_to_dict(df_a, df_b):
    merged_df = (pd.merge(df_a, df_b, how="outer"))
    merged_df.fillna(0, inplace=True)
    return merged_df.to_dict('records')


def decode_googlegeostr(point_str):
    '''Decodes a polyline that has been encoded using Google's algorithm
    http://code.google.com/apis/maps/documentation/polylinealgorithm.html
    This is a generic method that returns a list of (latitude, longitude)
    tuples.
    :param point_str: Encoded polyline string.
    :type point_str: string
    :returns: List of 2-tuples where each tuple is (latitude, longitude)
    :rtype: list
    '''

    # sone coordinate offset is represented by 4 to 5 binary chunks
    if point_str is None:
        return []

    if point_str == "":
        return []

    coord_chunks = [[]]
    for char in point_str:

        # convert each character to decimal from ascii
        value = ord(char) - 63

        # values that have a chunk following have an extra 1 on the left
        split_after = not (value & 0x20)
        value &= 0x1F

        coord_chunks[-1].append(value)

        if split_after:
            coord_chunks.append([])

    del coord_chunks[-1]

    coords = []

    for coord_chunk in coord_chunks:
        coord = 0

        for i, chunk in enumerate(coord_chunk):
            coord |= chunk << (i * 5)

        # there is a 1 on the right if the coord is negative
        if coord & 0x1:
            coord = ~coord  # invert
        coord >>= 1
        coord /= 100000.0

        coords.append(coord)

    # convert the 1 dimensional list to a 2 dimensional list and offsets to
    # actual values
    points = []
    prev_x = 0
    prev_y = 0
    for i in range(0, len(coords) - 1, 2):
        if coords[i] == 0 and coords[i + 1] == 0:
            continue
        prev_x += coords[i + 1]
        prev_y += coords[i]
        # a round to 6 digits ensures that the floats are the same as when
        # they were encoded
        points.append((round(prev_x, 6), round(prev_y, 6)))
    return points
