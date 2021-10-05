import os
import pandas as pd
import pdfkit
from datetime import datetime, timedelta
from .report_base import ReportBase
from .getRawDataLib import StationCenter
from jinja2 import Environment, FileSystemLoader


def parsing_df_for_user(report: pd.DataFrame):
    main_report = report.copy()  # 開始處裡準點報表
    main_report.index += 1  # index from 1
    main_report.rename(columns={'carno': '車牌號碼',
                                'count_of_runs': '執行班次數量',
                                'count_of_traveled_stop': '經過站牌總數',
                                }, inplace=True)

    return main_report


class BusDepartureCountReport(ReportBase):
    """
        顯示日期內有哪些車牌有出車，各執行了多少班，共經過多少站牌。
    """
    title = "發車次數統計一覽表"
    simple_description = '顯示日期內有哪些車牌有出車，各執行了多少班，共經過多少站牌。'

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.start_time = None
        self.end_time = None
        self.drove_bus = []
        self.report = None

    def generate_report(self, start_time: datetime, end_time: datetime = None, **kwargs):
        # setting time range
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is None:
            end_time = start_time
        else:
            assert end_time >= start_time
        self.end_time = end_time
        self.report = pd.DataFrame(columns=['carno', 'count_of_runs', 'count_of_traveled_stop'])

        # getting all carno
        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.report = station_center.get_runs_count_by_date(start_time=self.start_time,end_time=self.end_time)
        station_center.disconnect()
        self.report['count_of_runs'] = self.report['count_of_runs'].astype('int')
        self.report['count_of_traveled_stop'] = self.report['count_of_traveled_stop'].astype('int')

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)


