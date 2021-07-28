import logging
import os
import pandas as pd
import pdfkit
from datetime import datetime, timedelta
from .route_schedule_departure_report import RouteScheduleDepartureReport
from .report_base import ReportBase
from jinja2 import Environment, FileSystemLoader


def parsing_df_for_user(report: pd.DataFrame):
    main_report = report.copy()  # 開始處裡準點報表
    if main_report.empty:
        main_report = pd.DataFrame(columns=['日期', '結束日期', '應發車次數', '漏班次數',
                                            '非首站發車次數', '脫班次數', '正常發車次數', '準點率'])
    else:
        main_report.loc[0, 'start_time'] = main_report.loc[0, 'start_time'].strftime("%Y-%m-%d")
        main_report.loc[0, 'end_time'] = main_report.loc[0, 'end_time'].strftime("%Y-%m-%d")
        main_report.loc[0, 'on_time_rate'] = '{:.1%}'.format(main_report.loc[0, 'on_time_rate'])
        sum_column = main_report["early_departure"] + main_report["delay_departure"]
        main_report["early_delay"] = sum_column

        main_report = main_report[['start_time', 'end_time', 'duty_count', 'off_duty', 'not_from_first_stop',
                                   'early_delay', 'on_time_departure', 'on_time_rate']]

        main_report.rename(columns={'start_time': '日期',
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


class RouteOnTimeRateReport(ReportBase):
    """
        統計一個路線的時間內的班次發車情形，並計算準點率。
        包含有多少正常發車，多少漏班，早發，晚發。
        預設超過表定+-20min中算漏班; 預設準點時間為早1 min~晚5 min

        report schema:{
            'start_time': '資料統計的起始時間',
            'end_time': '資料統計的結束時間',
            'duty_count': '統計時間內的班次數量',
            'off_duty': '統計時間內, 沒有對應發車紀錄的班次',
            'not_from_first_stop': '統計時間內, 沒有從首站發車的班次數量',
            'early_departure': '統計時間內且從首站發車，過早發車的班次數量',
            'delay_departure': '統計時間內且從首站發車, 過晚發車的班次數量',
            'on_time_departure': '統計時間內且從首站發車, 正常時間發車的班次數量',
            'on_time_rate':'on_time_departure / duty_count',
        }

        * 'duty_count' = 'off_duty' + 'not_from_first_stop' + 'early_departure' + 'delay_departure' + 'on_time_departure'

    """

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = '路線準點率'
        self.start_time = None
        self.end_time = None
        self.rid = None
        self.rid_name = None
        self.vid = None
        self.vid_ch_name = None

    def generate_report(self, start_time: datetime, rid: int, off_duty_tol: int = 1200,
                        early_tol: int = 60, delay_tol: int = 300, end_time: datetime = None, **kwargs):
        '''
        input:
            start_time: 紀錄開始時間，以每日00:00開始計算。
            off_duty_tol: (秒) 若該班車與最接近的發車時間超過此，則為漏班，這趟車就不算在班次中。預設為1200
            early_tol: (秒) 若發車時間早於此秒數，則視為過早發車。預設為60
            delay_tol: (秒) 若發車時間晚於此秒數，則視為過晚發車。預設為300
            end_time: 紀錄結束時間，可不填入，則預設為start_time當天。
        '''
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.rid = rid

        route_schedule_departure_report = RouteScheduleDepartureReport(
            centerDB_conn_options=self._centerDB_conn_options,
            drivelogDB_conn_options=self._drivelogDB_conn_options)
        route_schedule_departure_report.generate_report(start_time=self.start_time, rid=self.rid,
                                                        off_duty_tol=off_duty_tol,
                                                        early_tol=early_tol, delay_tol=delay_tol, end_time=end_time)
        self.rid_name = route_schedule_departure_report.rid_name
        self.vid = route_schedule_departure_report.vid
        self.vid_ch_name = route_schedule_departure_report.vid_ch_name

        self.report = pd.DataFrame(columns=['start_time', 'end_time', 'duty_count', 'off_duty', 'not_from_first_stop',
                                            'early_departure', 'delay_departure', 'on_time_departure', 'on_time_rate'])

        # 非首站發車不算準點
        self.report.loc[0, 'start_time'] = self.start_time
        self.report.loc[0, 'end_time'] = self.end_time
        self.report.loc[0, 'duty_count'] = len(route_schedule_departure_report.report)
        self.report.loc[0, 'off_duty'] = (route_schedule_departure_report.report['bus_count'] == 0).sum()
        self.report.loc[0, 'not_from_first_stop'] = (
                route_schedule_departure_report.report['from_first_stop'] == False
        ).sum()

        from_first_stop = route_schedule_departure_report.report[
            route_schedule_departure_report.report['from_first_stop'] == True
        ]

        self.report.loc[0, 'early_departure'] = (from_first_stop['early_bus_count'] != 0).sum()
        self.report.loc[0, 'delay_departure'] = (from_first_stop['delay_bus_count'] != 0).sum()
        self.report.loc[0, 'on_time_departure'] = (from_first_stop['on_time_bus_count'] != 0).sum()
        self.report.loc[0, 'on_time_rate'] = 0
        if self.report.loc[0, 'duty_count'] != 0: # duty count might be 0
            self.report.loc[0, 'on_time_rate'] = self.report.loc[0, 'on_time_departure'] \
                                                 / self.report.loc[0, 'duty_count']

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)

    def view_in_html(self):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")

        df_for_user = parsing_df_for_user(self.report)
        template_vars = {
            "title": self.title,
            "rid": self.rid_name,
            "vid_ch_name": self.vid_ch_name,
            "start_date": self.start_time.strftime("%Y-%m-%d"),
            "end_date": self.end_time.strftime("%Y-%m-%d"),
            "report": df_for_user.to_html(index=False),
        }
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("reports/templates/reports/route_on_time_rate_report_template.html")
        html_out = template.render(template_vars)

        return html_out

    def save_as_pdf(self, over_write: bool = False):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")
        dir_name = "bucket/" + self.title + "/" + self.start_time.strftime("%Y-%m-%d")
        file_name = str(self.rid) + ".pdf"

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