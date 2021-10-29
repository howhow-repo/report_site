# -*- encoding: utf-8 -*-
from queue import Queue
import json
import os
import threading

import pandas as pd

from django.http import HttpResponse
from django.shortcuts import redirect
from decouple import config
from django.template import loader
from django.urls import reverse

from app.reportsLib import StationCenter, StopToStopResult
from map.form import ParaInput

CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed'),
    'segment': 'map',
    'title': '數據地理資訊',
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

    threads = []
    que = Queue()

    def stop_staytime_job(report_name, hour_begin, hour_end):
        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        sr.connect()
        rp = (sr.get_default_stop_to_stop_by_rid(**{**para_received,
                                                    'hour_begin': hour_begin,
                                                    'hour_end': hour_end}))
        sr.disconnect()
        return {report_name: rp}

    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_morning', TIMERANGE['morning']['b'], TIMERANGE['morning']['e'])), args=(que, ())))
    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_noon', TIMERANGE['noon']['b'], TIMERANGE['noon']['e'])), args=(que, ())))
    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_afternoon', TIMERANGE['afternoon']['b'], TIMERANGE['afternoon']['e'])), args=(que, ())))
    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_evening', TIMERANGE['evening']['b'], TIMERANGE['evening']['e'])), args=(que, ())))
    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_night', TIMERANGE['night']['b'], TIMERANGE['night']['e'])), args=(que, ())))
    threads.append(threading.Thread(target=lambda q, arg1: q.put(
        stop_staytime_job('rp_latenight', TIMERANGE['latenight']['b'], TIMERANGE['latenight']['e'])), args=(que, ())))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    reports = {}
    while not que.empty():
        result = que.get()
        for key, value in result.items():
            reports[key] = value

    context['geojson_line'] = str(json.dumps(geojson_line))
    context['stop_location'] = stop_locations_df.to_dict('records')
    context['geojson_morning'] = merge_df_to_dict(stop_locations_df, reports['rp_morning'])
    context['geojson_noon'] = merge_df_to_dict(stop_locations_df, reports['rp_noon'])
    context['geojson_afternoon'] = merge_df_to_dict(stop_locations_df, reports['rp_afternoon'])
    context['geojson_evening'] = merge_df_to_dict(stop_locations_df, reports['rp_evening'])
    context['geojson_night'] = merge_df_to_dict(stop_locations_df, reports['rp_night'])
    context['geojson_latenight'] = merge_df_to_dict(stop_locations_df, reports['rp_latenight'])
    context['route_ch_name'] = route_ch_name
    context['avg_lon'] = sum(stop_locations_df['lon'].tolist()) / len(stop_locations_df['lon'].tolist())
    context['avg_lat'] = sum(stop_locations_df['lat'].tolist()) / len(stop_locations_df['lat'].tolist())
    context['rid'] = rid
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
