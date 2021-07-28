import os
from .report_base import ReportBase
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
import pdfkit
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger()

def parsing_df_for_user(report: pd.DataFrame):
    if report.empty:
        return pd.DataFrame(columns=['表定發車時間', '車號', '公車發車時間', '發車時間差(分)', '到站率'])

    main_report = report.copy()  # 開始處裡準點報表
    main_report.index += 1  # index from 1
    try:
        main_report['run_stop_rate'] = pd.Series(["{0:.1f}%".format(val * 100) for val in main_report['run_stop_rate']],
                                                index=main_report.index)
    except:
        logger.error("unable to re-format column 'run_stop_rate'")

    main_report = main_report[['starttime', 'carno', 'bus_departure_time', 'departure_timedelta', 'run_stop_rate']]

    main_report.rename(columns={'starttime': '表定發車時間',
                                'carno': '車號',
                                'bus_departure_time': '公車發車時間',
                                'departure_timedelta': '發車時間差(s)',
                                'run_stop_rate': '到站率',
                                }, inplace=True)

    return main_report


class RouteDepartureReport(ReportBase):
    '''
        呈現一個路線在時間內的發車紀錄。
        report schema:[
            'rid': 'route id,
            'direct' ,
            'cid',
            'did',
            'starttime',
            'endtime',
            'carno',
            'vid',
            'bus_departure_time',
            'departure_timedelta',
            'run_stop_rate',
            'error_code'
        ]
    '''

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "路線發車紀錄"
        self.start_time = None
        self.end_time = None
        self.rid = None
        self.rid_name = None

    def generate_report(self, start_time: datetime, rid: int, end_time: datetime = None, **kwargs):
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.rid = rid
        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.rid_name = station_center.get_route_ch_name(rid=self.rid)
        report_schema = pd.DataFrame(columns=['rid', 'direct', 'cid', 'did', 'starttime', 'endtime', 'carno', 'vid',
                                              'bus_departure_time', 'departure_timedelta', 'run_stop_rate',
                                              'error_code'])

        self.report = station_center.get_schedule_logs_by_rid(rid=self.rid,
                                                              start_time=start_time,
                                                              end_time=end_time)

        # 避免撈回來的班表(schedule)中，'starttime'有重複，但屬於不同的schedule_id
        self.report.drop_duplicates(subset='starttime',inplace=True)

        station_center.disconnect()

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)

    def view_in_html(self):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")

        df_for_user = parsing_df_for_user(self.report)
        template_vars = {
            "title": self.title,
            "rid": str(self.rid_name),
            "start_date": self.start_time.strftime("%Y-%m-%d"),
            "end_date": self.end_time.strftime("%Y-%m-%d"),
            "report": df_for_user.to_html(index=False),
        }
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("reports/templates/reports/route_departure_report_template.html")
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
