import os

import numpy as np
import pandas as pd
import pdfkit
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
from .report_base import ReportBase
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger()


def parsing_df_for_user(report: pd.DataFrame):
    main_report = report.copy()  # 開始處裡準點報表
    if main_report.empty:
        main_report = pd.DataFrame(columns=['路線名稱', '日期', '結束日期', '應發車次數', '漏班次數',
                                            '非首站發車次數', '脫班次數', '正常發車次數', '準點率'])
    else:
        main_report['on_time_rate'] = pd.Series(["{0:.1f}%".format(val * 100) for val in main_report['on_time_rate']],
                                                index=main_report.index)
        sum_column = main_report["early_departure"] + main_report["delay_departure"]
        main_report["early_delay"] = sum_column

        main_report = main_report[['rid', 'rid_name', 'duty_count', 'off_duty', 'not_from_first_stop',
                                   'early_delay', 'on_time_departure', 'on_time_rate']]

        main_report.replace([np.nan, None, "nan%"], '', inplace=True)

        main_report.rename(columns={'rid_name': '路線名稱',
                                    'start_time': '日期',
                                    'end_time': '結束日期',
                                    'duty_count': '應發車次數',
                                    'off_duty': '漏班次數',
                                    'not_from_first_stop': '非首站發車次數',
                                    'early_delay': '脫班次數',
                                    'on_time_departure': '正常發車次數',
                                    'on_time_rate': '準點率'
                                    }, inplace=True)

    main_report.index += 1  # index from 1
    return main_report


class TotalOnTimeRateReport(ReportBase):
    """
        以個路線準點報表(route_on_time_rate_report_rnBase)為基礎，建立各路線準點率的報表。
    """
    title = "準點率一覽表"
    simple_description = '以各路線準點報表(單一路線準點率)為基礎，建立各路線準點率的報表。'

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.start_time = None
        self.end_time = None
        self.total_rids = []

    def generate_report(self, start_time: datetime, off_duty_tol: int = 1200, early_tol: int = 60,
                        delay_tol: int = 300, end_time: datetime = None, **kwargs):
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.total_rids = station_center.get_rid_list_by_date(start_time=start_time, end_time=end_time)
        report = station_center.get_on_time_rate(start_time=start_time, end_time=end_time,
                                                 off_duty_tol=off_duty_tol, early_tol=early_tol, delay_tol=delay_tol)
        self.report = report
        station_center.disconnect()
        return self.report

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)
