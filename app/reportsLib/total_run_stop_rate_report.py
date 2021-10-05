import os

import numpy as np

from .report_base import ReportBase
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
import pdfkit
import pandas as pd
from jinja2 import Environment, FileSystemLoader


def parsing_df_for_user(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return pd.DataFrame(columns=['路線名稱', '班次數量', '平均到站率'])

    main_report = report.copy()  # 開始處裡準點報表
    main_report.index += 1  # index from 1

    main_report['avg_run_stop_rate'] = pd.Series(
        ["{0:.1f}%".format(val * 100) for val in main_report['avg_run_stop_rate']],
        index=main_report.index)
    main_report = main_report.astype({"runs_count": int})  # format each

    main_report = main_report[['rid','rid_ch_name', 'runs_count', 'avg_run_stop_rate']]

    main_report.replace([np.nan, None, "nan%"], '', inplace=True)

    main_report.rename(columns={'rid_ch_name': '路線名稱',
                                'runs_count': '班次數量',
                                'avg_run_stop_rate': '平均到站率',
                                }, inplace=True)

    return main_report


class TotalRunStopRateReport(ReportBase):
    """
        各路線時間內的平均班次到站率。
    """
    title = "平均到站率一覽表"
    simple_description = '各路線時間內的平均班次到站率。'

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.vid = None
        self.vid_ch_name = None
        self.start_time = None
        self.end_time = None
        self.total_rids = []

    def generate_report(self, start_time: datetime, end_time: datetime = None, **kwargs):
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.report = pd.DataFrame({
            'rid': [],
            'rid_ch_name': [],
            'runs_count': [],
            'avg_run_stop_rate': [],
        })

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()

        rids_in_schedule = station_center.get_rid_list_by_date(start_time=self.start_time, end_time=self.end_time)
        self.total_rids = str(rids_in_schedule)
        self.total_rids = self.total_rids.replace('[', '(')
        self.total_rids = self.total_rids.replace(']', ')')
        self.report = station_center.get_run_stop_rate(start_time=self.start_time, end_time=self.end_time)

        station_center.disconnect()

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)
