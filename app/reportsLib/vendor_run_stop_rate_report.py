import os

import numpy as np

from .report_base import ReportBase
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
import pdfkit
import pandas as pd
from jinja2 import Environment, FileSystemLoader


def to_sqllist(l: list) -> str:
    l = str(l)
    l = l.replace('[', '(')
    l = l.replace(']', ')')
    return l


def parsing_df_for_user(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return pd.DataFrame(columns=['路線名稱', '班次數量', '平均到站率'])

    main_report = report.copy()  # 開始處裡準點報表
    main_report.index += 1  # index from 1

    main_report['avg_run_stop_rate'] = pd.Series(
        ["{0:.1f}%".format(val * 100) for val in main_report['avg_run_stop_rate']],
        index=main_report.index)
    main_report = main_report.astype({"runs_count": int})  # format each

    main_report = main_report[['rid', 'rid_ch_name', 'runs_count', 'avg_run_stop_rate']]

    main_report.replace([np.nan, None, "nan%"], '', inplace=True)

    main_report.rename(columns={'rid_ch_name': '路線名稱',
                                'runs_count': '班次數量',
                                'avg_run_stop_rate': '平均到站率',
                                }, inplace=True)

    return main_report


class VendorRunStopRateReport(ReportBase):
    """
        以單一營運商為單位建立各路線平均班次到站率。
    """

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "營運商 平均路線到站率一覽表"
        self.simple_description = '以單一營運商為單位建立各路線平均班次到站率。'
        self.vid = None
        self.vid_ch_name = None
        self.start_time = None
        self.end_time = None
        self.total_rids = []

    def generate_report(self, vid: int, start_time: datetime, end_time: datetime = None, **kwargs):
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.vid = vid
        self.report = pd.DataFrame({
            'rid': [],
            'rid_ch_name': [],
            'runs_count': [],
            'avg_run_stop_rate': [],
        })

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.vid_ch_name = station_center.get_vid_ch_name(self.vid)
        self.sub_title = "營運商：" + self.vid_ch_name

        rids_of_vid = station_center.get_rids_list_by_vid(self.vid)
        rids_in_schedule = station_center.get_rid_list_by_date(start_time=self.start_time, end_time=self.end_time)

        self.total_rids = list(set(rids_of_vid).intersection(rids_in_schedule))
        if len(self.total_rids) != 0:
            total_rids_sqllist = to_sqllist(self.total_rids)
            self.report = station_center.get_run_stop_rate(start_time=self.start_time, end_time=self.end_time,
                                                           other_filter=f"where rid in {total_rids_sqllist}")
        station_center.disconnect()
        return self.report

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)
