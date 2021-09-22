import os

import numpy as np
import pandas as pd
import pdfkit
from datetime import datetime,timedelta
from .getRawDataLib import StationCenter
from .report_base import ReportBase
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger()

report_schema = ['rid', 'rid_ch_name', 'schedule_departure_time',
                 'bus_departure_time', 'bus_departure_stop', 'bus_departure_sne',
                 'departure_timedelta', 'traveled_stops_count', 'bus_arrival_time',
                 'bus_arrival_stop', 'bus_arrival_sne', 'error_code']


def parsing_df_for_user(report: pd.DataFrame):
    if report.empty:
        return pd.DataFrame(columns=['路線名稱', '日期', '結束日期', '應發車次數', '未發車次數',
                                     '過早發車次數', '過晚發車次數', '正常發車次數', '準點率'])

    main_report = report.copy()  # 開始處裡準點報表
    main_report.index += 1  # index from 1
    main_report = main_report[['rid_ch_name', 'schedule_departure_time', 'bus_departure_time', 'departure_timedelta',
                               'bus_departure_sne', 'bus_arrival_sne', 'route_stops_count', 'traveled_stops_count',
                               'bus_arrival_time', 'run_stop_rate', ]]  # columns need

    main_report = main_report.astype({"traveled_stops_count": int,
                                      "route_stops_count": int})  # format each
    main_report['run_stop_rate'] = pd.Series(["{0:.1f}%".format(val * 100) for val in main_report['run_stop_rate']],
                                             index=main_report.index)  # format to %

    main_report.replace([np.nan, None, "nan%"], '', inplace=True)

    main_report.rename(columns={'rid_ch_name': '路線名稱',
                                'schedule_departure_time': '表定發車時間',
                                'bus_departure_time': '發車時間',
                                'bus_departure_sne': '發車站站名',
                                'bus_arrival_sne': '到站站名',
                                'route_stops_count': '應經過站牌數',
                                'departure_timedelta': '發車時間誤差(s)',
                                'traveled_stops_count': '經過站牌數',
                                'bus_arrival_time': '終點站到站時間',
                                'run_stop_rate': '到站率',
                                }, inplace=True)

    return main_report


class BusDayRunReport(ReportBase):
    '''
        顯示一台車(車號)，在日期內執行過哪些班次任務，及各班次執行狀態。
        資料來源為drive log來自MongoDB

        report schema:{
            'rid',
            'rid_ch_name',
            'schedule_departure_time':'表定發車時間',
            'bus_departure_time':'實際發車時間',
            'bus_departure_stop':'實際發車站',
            'bus_departure_sne':'實際發車站站名',
            'departure_timedelta',
            'traveled_stops_count',
            'bus_arrival_time',
            'bus_arrival_stop',
            'error_code'
        }
    '''
    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "公車任務執行紀錄"
        self.simple_description = '顯示一台車(車號)，在日期內執行過哪些班次任務，及各班次執行狀態。'
        self.start_time = None
        self.end_time = None
        self.carno = None

    def generate_report(self, start_time: datetime, carno: str, end_time: datetime = None, **kwargs):
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.carno = carno
        self.sub_title = "車號："+self.carno
        empty_report = pd.DataFrame(columns=report_schema)
        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        bus_run_logs = station_center.get_run_logs_by_carno(carno=self.carno,start_time=start_time,end_time=end_time)
        station_center.disconnect()

        self.report = empty_report.append(bus_run_logs,ignore_index=True)

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)

    def view_in_html(self):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")

        df_for_user = parsing_df_for_user(self.report)
        template_vars = {
            "title": self.title,
            "start_date": self.start_time.strftime("%Y-%m-%d"),
            "carno": self.carno,
            "end_date": self.end_time.strftime("%Y-%m-%d"),
            "report": df_for_user.to_html(),
        }
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("reports/templates/reports/bus_day_run_report_template.html")
        html_out = template.render(template_vars)

        return html_out

    def save_as_pdf(self, over_write: bool = False):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")
        dir_name = "bucket/" + self.title + "/" + self.start_time.strftime("%Y-%m-%d")
        file_name = str(self.carno) + ".pdf"

        if not os.path.exists(dir_name):  # return nothing if file exist
            os.makedirs(dir_name)
        else:
            if (os.path.isfile(dir_name + "/" + file_name)) and over_write is False:
                return 0

        html = self.view_in_html()

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'no-outline': None,
            'enable-local-file-access': '',
        }
        pdfkit.from_string(html, dir_name + "/" + file_name, options=options)
