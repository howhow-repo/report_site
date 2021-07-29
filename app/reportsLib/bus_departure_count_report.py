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
                                'count_of_travled_stop': '經過站牌總數',
                                }, inplace=True)

    return main_report


class BusDepartureCountReport(ReportBase):
    '''
        顯示日期內有哪些車牌有出車，各執行了多少班，共經過多少站牌。
    '''

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "發車次數統計一覽表"
        self.simple_description = '顯示日期內有哪些車牌有出車，各執行了多少班，共經過多少站牌。'
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
        self.report = pd.DataFrame(columns=['carno', 'count_of_runs', 'count_of_travled_stop'])
        self.report['count_of_runs'] = self.report['count_of_runs'].astype('int')
        self.report['count_of_travled_stop'] = self.report['count_of_travled_stop'].astype('int')

        # getting all carno
        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.drove_bus = station_center.get_carno_list_departed_by_date(start_time=start_time, end_time=end_time)
        print(f'There r {len(self.drove_bus)} buses to check')

        # calculate & generate report

        for i, carno in enumerate(self.drove_bus):
            print(f'----parsing carno {carno}----')
            bus_logs = station_center.get_run_logs_by_carno(carno, start_time=start_time, end_time=end_time)
            new_row = {
                'carno': carno,
                'count_of_runs': len(bus_logs),
                'count_of_travled_stop': bus_logs['traveled_stops_count'].sum()
            }
            self.report = self.report.append(new_row, ignore_index=True)
            print(f'parsing done:{i}')

        station_center.disconnect()

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
        template = env.get_template("reports/templates/reports/bus_departure_count_report.html")
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
