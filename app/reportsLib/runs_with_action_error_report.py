import os
import pandas as pd
import pdfkit
from datetime import datetime, timedelta
from .report_base import ReportBase
from .getRawDataLib import StationCenter
from jinja2 import Environment, FileSystemLoader


def parsing_df_for_user(report: pd.DataFrame):
    if report.empty:
        return pd.DataFrame(columns=['路線名稱', '車牌號碼', '發車時間', '發車站名',
                                     '本日查無班次','非班次時間內發車','非首站發車','無到達終點站','到站率'])
    main_report = report.copy()  # 開始處裡準點報表
    main_report['run_stop_rate'] = pd.Series(["{0:.1f}%".format(val * 100) for val in main_report['run_stop_rate']],
                                             index=main_report.index)

    main_report[['no_schedule_today','out_of_schedule_range','not_from_first_stop','not_arrive_to_last_stop']] \
        = main_report[['no_schedule_today','out_of_schedule_range','not_from_first_stop','not_arrive_to_last_stop']].replace([True, False], ['V', ''])

    main_report = main_report[
        ['rid', 'rid_name', 'carno', 'bus_departure_time', 'bus_departure_sne', 'no_schedule_today',
         'out_of_schedule_range', 'not_from_first_stop', 'not_arrive_to_last_stop','run_stop_rate']
    ]

    main_report.rename(columns={'rid_name': '路線名稱',
                                'carno': '車牌號碼',
                                'bus_departure_time': '發車時間',
                                'bus_departure_sne': '發車站名',
                                'no_schedule_today': '本日查無班次',
                                'out_of_schedule_range': '非班次時間內發車',
                                'not_from_first_stop': '非首站發車',
                                'not_arrive_to_last_stop': '未達達終點站',
                                'run_stop_rate': '到站率',
                                }, inplace=True)

    main_report.index += 1  # index from 1
    return main_report

class RunsWithActionErrorReport(ReportBase):
    '''
        顯示班車行進中有異常的異常方式：
            ＊ 發車當日無該路線班次
            ＊ 非班次時間內發車
            ＊ 非首站發車
            ＊ 未達達終點站
            ＊ 到站率
    '''
    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "公車班次執行異常一覽表"
        self.start_time = None
        self.end_time = None
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

        self.report = pd.DataFrame(columns=['rid','rid_name','carno','cid','vid','did',
                                            'bus_departure_time','bus_departure_stop','bus_departure_sne',
                                            'run_stop_rate','weekdayType',
                                            'no_schedule_today','out_of_schedule_range',
                                            'not_from_first_stop','not_arrive_to_last_stop',
                                            'error_code'])

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        error_runs = station_center.get_runs_with_error(start_time=start_time, end_time=end_time)
        station_center.disconnect()

        self.report = pd.concat([self.report,error_runs])
        self.report[['no_schedule_today','out_of_schedule_range','not_from_first_stop','not_arrive_to_last_stop']] = False

        self.report.loc[(self.report['error_code'] & 1) != 0, 'no_schedule_today'] = True
        self.report.loc[(self.report['error_code'] & 2) != 0, 'out_of_schedule_range'] = True
        self.report.loc[(self.report['error_code'] & 32) != 0, 'not_from_first_stop'] = True
        self.report.loc[(self.report['error_code'] & 64) != 0, 'not_arrive_to_last_stop'] = True

        i =  self.report[( self.report['no_schedule_today'] == False)
               &( self.report['out_of_schedule_range'] == False)
               &( self.report['not_from_first_stop'] == False)
               &( self.report['not_arrive_to_last_stop'] == False)
        ].index
        self.report.drop(i, inplace=True)
        self.report.reset_index()

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)

    def view_in_html(self):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")

        df_for_user = parsing_df_for_user(self.report)

        template_vars = {
            "title": self.title,
            "start_date": self.start_time.strftime("%Y-%m-%d"),
            "end_date": self.end_time.strftime("%Y-%m-%d"),
            "report": df_for_user.to_html(),
        }

        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("reports/templates/reports/runs_with_action_error_report_template.html")
        html_out = template.render(template_vars)

        return html_out

    def save_as_pdf(self, over_write: bool = False):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")
        dir_name = "bucket/" + self.title
        file_name = self.start_time.strftime("%Y-%m-%d") + ".pdf"

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


