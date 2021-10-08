import ast
import json, os
from datetime import datetime
from typing import Type

import pandas

from app.reportsLib import StopToStopResult


class ComparisonReportBase:
    rtype = None
    title = None
    description = ''
    paras_comm = []
    paras_A = []
    paras_B = []
    compare_value = ''
    chart_type = ''
    func = None

    def __init__(self):
        self.result_A = pandas.DataFrame()
        self.result_B = pandas.DataFrame()
        self.chart_A = {'paras': {}, 'result': {}}
        self.chart_B = {'paras': {}, 'result': {}}

    def split_request_paras(self, request_paras):
        for r in request_paras:
            if r in self.paras_A or r in self.paras_comm:
                self.chart_A['paras'].update({r: request_paras[r]})
            if r in self.paras_B or r in self.paras_comm:
                self.chart_B['paras'].update({r: request_paras[r]})

    def format_paras(self, chart):
        if 'rid_stat' in chart['paras']:
            chart['paras'].update({
                "rid": (ast.literal_eval(chart['paras']['rid_stat']))[0],
                "rid_name": (ast.literal_eval(chart['paras']['rid_stat']))[1],
            })
            del chart['paras']['rid_stat']

        if 'weekday_A' in chart['paras']:
            chart['paras'].update({
                "weekday": chart['paras']['weekday_A']
            })
            del chart['paras']['weekday_A']

        if "weekday_B" in chart['paras']:
            chart['paras'].update({
                "weekday": chart['paras']['weekday_B']
            })
            del chart['paras']['weekday_B']

        if "weekdayType_A" in chart['paras']:
            chart['paras'].update({
                "weekdayType": chart['paras']['weekdayType_A']
            })
            del chart['paras']['weekdayType_A']

        if "weekdayType_B" in chart['paras']:
            chart['paras'].update({
                "weekdayType": chart['paras']['weekdayType_B']
            })
            del chart['paras']['weekdayType_B']

        print(chart)

    def calculate_results(self):
        if self.func is None:
            raise NotImplementedError("function undefined")

        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        sr.connect()

        rpA = getattr(sr, self.func)(**self.chart_A['paras'])
        rpA.fillna(0, inplace=True)

        rpB = getattr(sr, self.func)(**self.chart_B['paras'])
        rpB.fillna(0, inplace=True)

        sr.disconnect()

        self.result_A = rpA
        self.result_B = rpB
        self.chart_A.update({'result': rpA.to_dict('records')})
        self.chart_B.update({'result': rpB.to_dict('records')})


class TraveltimeWeekday(ComparisonReportBase):
    rtype = 'traveltime_weekday'
    title = '行駛時間與星期比較表'
    description = '比較不同星期時，站與站之間的行駛時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekday_A']
    paras_B = ['weekday_B']
    compare_value = 'avg_arrival_time_spent'
    chart_type = 'stops'
    func = 'get_default_stop_to_stop_by_rid'


class TraveltimeWeekdayType(ComparisonReportBase):
    rtype = 'traveltime_weekdayType'
    title = '行駛時間與日種類比較表'
    description = '比較不同種日時，站與站之間的行駛時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekdayType_A']
    paras_B = ['weekdayType_B']
    compare_value = 'avg_arrival_time_spent'
    chart_type = 'stops'
    func = 'get_default_stop_to_stop_by_rid'


class StaytimeWeekday(ComparisonReportBase):
    rtype = 'staytime_weekday'
    title = '站內停留時間與星期比較表'
    description = '比較不同星期時，站內停留時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekday_A']
    paras_B = ['weekday_B']
    compare_value = 'avg_stay_time'
    chart_type = 'stops'
    func = 'get_default_stop_to_stop_by_rid'


class StaytimeWeekdayType(ComparisonReportBase):
    rtype = 'staytime_weekdayType'
    title = '站內停留時間與日種類比較表'
    description = '比較不同種日時，站內停留時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekdayType_A']
    paras_B = ['weekdayType_B']
    compare_value = 'avg_stay_time'
    chart_type = 'stops'
    func = 'get_default_stop_to_stop_by_rid'


class RsidTraveltimeWeekday(ComparisonReportBase):
    rtype = 'rsid_traveltime_weekday'
    title = '單站行駛時間與星期比較表'
    description = '比較兩站之間，在不同星期下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ]
    paras_A = ['weekday_A']
    paras_B = ['weekday_B']
    compare_value = 'avg_arrival_time_spent'
    chart_type = 'hour'
    func = 'get_stop_to_stop_hourly_by_rsid'


class RsidTraveltimeWeekdayType(ComparisonReportBase):
    rtype = 'rsid_traveltime_weekdayType'
    title = '單站行駛時間與日種類比較表'
    description = '比較兩站之間，在不同日種類下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ]
    paras_A = ['weekdayType_A']
    paras_B = ['weekdayType_B']
    compare_value = 'avg_arrival_time_spent'
    chart_type = 'hour'
    func = 'get_stop_to_stop_hourly_by_rsid'


class RsidStaytimeWeekday(ComparisonReportBase):
    rtype = 'rsid_staytime_weekday'
    title = '單站停留時間與星期比較表'
    description = '比較同一站，在不同星期下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ]
    paras_A = ['weekday_A']
    paras_B = ['weekday_B']
    compare_value = 'avg_stay_time'
    chart_type = 'hour'
    func = 'get_stop_to_stop_hourly_by_rsid'


class RsidStaytimeWeekdayType(ComparisonReportBase):
    rtype = 'rsid_staytime_weekdayType'
    title = '單站停留時間與日種類比較表'
    description = '比較同一站，在不同日種類下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ]
    paras_A = ['weekdayType_A']
    paras_B = ['weekdayType_B']
    compare_value = 'avg_stay_time'
    chart_type = 'hour'
    func = 'get_stop_to_stop_hourly_by_rsid'


class ComparisonReportCenter:
    report_list = [
        TraveltimeWeekday,
        TraveltimeWeekdayType,
        StaytimeWeekday,
        StaytimeWeekdayType,
        RsidStaytimeWeekdayType,
        RsidStaytimeWeekday,
        RsidTraveltimeWeekdayType,
        RsidTraveltimeWeekday,
    ]

    @classmethod
    def list_of_dict(cls) -> list:
        l = []
        for r in cls.report_list:
            t = {}
            r_attr = [a for a in dir(r) if not a.startswith('__')]
            for a in r_attr:
                t.update({a: getattr(r, a)})
            l.append(t)
        return l

    @classmethod
    def find_report_type(cls, rtype: str) -> Type[ComparisonReportBase]:
        for r in cls.report_list:
            if rtype == r.rtype:
                return r
        return ComparisonReportBase
