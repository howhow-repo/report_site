import pandas as pd
import pdfkit
import os

from .report_base import ReportBase
from .bus_departure_count_report import BusDepartureCountReport
from .bus_day_run_report import BusDayRunReport
from .route_departure_report import RouteDepartureReport
from .route_schedule_departure_report import RouteScheduleDepartureReport
from .vendor_route_on_time_rate_report import VendorRouteOnTimeRateReport
from .vendor_run_stop_rate_report import VendorRunStopRateReport
from .route_schedule_departure_count_report import RouteScheduleDepartureCountReport
from .route_on_time_rate_report import RouteOnTimeRateReport
from .total_on_time_rate_report import TotalOnTimeRateReport
from .total_run_stop_rate_report import TotalRunStopRateReport
from .runs_not_on_schedule_report import RunsNotOnScheduleReport
from .runs_with_action_error_report import RunsWithActionErrorReport
from .runs_with_log_error_report import RunsWithLogErrorReport


class ReportCenter(object):
    """
        a object that should able to call all kinds of reports
    """

    def __init__(self, centerDB_conn_options={}, drivelogDB_conn_options={}):
        self._drivelogDB_conn_options = drivelogDB_conn_options
        self._centerDB_conn_options = centerDB_conn_options
        self.report_list = self.report_list = {
            'bus_departure_count_report': BusDepartureCountReport,
            'bus_day_run_report': BusDayRunReport,
            'route_departure_report': RouteDepartureReport,
            'route_schedule_departure_report':RouteScheduleDepartureReport,
            'route_schedule_departure_count_report': RouteScheduleDepartureCountReport,
            'route_on_time_rate_report': RouteOnTimeRateReport,
            'vendor_route_on_time_rate_report': VendorRouteOnTimeRateReport,
            'total_on_time_rate_report': TotalOnTimeRateReport,
            'vendor_run_stop_rate_report': VendorRunStopRateReport,
            'total_run_stop_rate_report': TotalRunStopRateReport,
            'runs_not_on_schedule_report': RunsNotOnScheduleReport,
            'runs_with_action_error_report': RunsWithActionErrorReport,
            'runs_with_log_error_report': RunsWithLogErrorReport,
            # TODO: remember to add report classes here
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
