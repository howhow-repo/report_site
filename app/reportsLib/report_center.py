import pandas as pd
import pdfkit
import os

from .report_base import ReportBase
from .bus_departure_count_report import BusDepartureCountReport
from .bus_day_run_report import BusDayRunReport
from .route_departure_report import RouteDepartureReport
from .vendor_route_on_time_rate_report import VendorRouteOnTimeRateReport
from .vendor_run_stop_rate_report import VendorRunStopRateReport
from .route_schedule_departure_report import RouteScheduleDepartureReport
from .route_on_time_rate_report import RouteOnTimeRateReport
from .totle_on_time_rate_report import TotleOnTimeRateReport
from .runs_not_on_schedule_report import RunsNotOnScheduleReport
from .runs_with_action_error_report import RunsWithActionErrorReport
from .runs_with_log_error_report import RunsWithLogErrorReport


class ReportCenter(object):
    '''
        a object that should able to call all kinds of reports
    '''

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        self._drivelogDB_conn_options = drivelogDB_conn_options
        self._centerDB_conn_options = centerDB_conn_options
        self.report_list = {
            'bus_departure_count_report': BusDepartureCountReport,
            'bus_day_run_report': BusDayRunReport,
            'route_departure_report': RouteDepartureReport,
            'vendor_route_on_time_rate_report': VendorRouteOnTimeRateReport,
            'vendor_run_stop_rate_report': VendorRunStopRateReport,
            'route_schedule_departure_report': RouteScheduleDepartureReport,
            'route_on_time_rate_report': RouteOnTimeRateReport,
            'totle_on_time_rate_report': TotleOnTimeRateReport,
            'runs_not_on_schedule_report': RunsNotOnScheduleReport,
            'runs_with_action_error_report': RunsWithActionErrorReport,
            'runs_with_log_error_report': RunsWithLogErrorReport,
            # TODO: remember to add report classes here
        }
        self.simple_description = {
            'bus_departure_count_report': '顯示日期內有哪些車牌有出車，各執行了多少班，共經過多少站牌。',
            'bus_day_run_report': '顯示一台車(車號)，在日期內執行過哪些班次任務，及各班次執行狀態。',
            'route_departure_report': '呈現一個路線在時間內的發車紀錄。',
            'vendor_route_on_time_rate_report': '以單一營運商為單位建立路線的準點率一覽報表。',
            'vendor_run_stop_rate_report': '以單一營運商為單位建立各路線平均班次到站率。',
            'route_schedule_departure_report': '以路線班次為基準，計算各班次有多少車，發車是否為準時。預設+-20min中即不算漏班;預設準點時間為早 1 min~晚 5 min',
            'route_on_time_rate_report': '統計一個路線的時間內的班次發車情形，並計算準點率。包含有多少正常發車，多少漏班，早發，晚發。',
            'totle_on_time_rate_report': '以個路線準點報表(route_on_time_rate_report_rnBase)為基礎，建立各路線準點率的報表。',
            'runs_not_on_schedule_report': '顯示時間內有多少車次是無對應的班次。',
            'runs_with_action_error_report': '顯示班車行進中有異常的異常方式。',
            'runs_with_log_error_report': '顯示班車行資訊回報有異常的異常方式。',
        }
        self.report = None
        self.report_type = None

    def list_reports(self):
        return list(self.report_list.keys())

    def create_empty_report(self, report_type) -> ReportBase:
        if report_type in self.report_list:
            sub_class = self.report_list[report_type]
            self.report = sub_class(centerDB_conn_options=self._centerDB_conn_options,
                                    drivelogDB_conn_options=self._drivelogDB_conn_options)
            self.report_type = report_type
            return self.report
        else:
            raise AttributeError(f"can not find this kind of report: {report_type}")

    def create_daily_report(self):
        pass
