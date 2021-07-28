import os
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

    main_report = main_report[['rid_ch_name', 'runs_count', 'avg_run_stop_rate']]
    main_report.rename(columns={'rid_ch_name': '路線名稱',
                                'runs_count': '班次數量',
                                'avg_run_stop_rate': '平均到站率',
                                }, inplace=True)

    return main_report


class VendorRunStopRateReport(ReportBase):
    '''
        以單一營運商為單位建立各路線平均班次到站率。
    '''
    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "營運商 平均路線到站率一覽表"
        self.vid = None
        self.vid_ch_name = None
        self.start_time = None
        self.end_time = None
        self.totle_rids = []

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

        rids_of_vid = station_center.get_rids_list_by_vid(self.vid)
        rids_in_schedule = station_center.get_rid_list_by_date(start_time=self.start_time, end_time=self.end_time)

        self.totle_rids = list(set(rids_of_vid).intersection(rids_in_schedule))

        for rid in self.totle_rids:
            rid_ch_name = station_center.get_route_ch_name(rid)
            run_stop_rate = station_center.get_run_stop_rate_by_rid(rid, self.start_time, self.end_time)
            runs_count = len(run_stop_rate)
            if run_stop_rate.empty:
                avg_run_stop_rate = 0
            else:
                avg_run_stop_rate = run_stop_rate['run_stop_rate'].mean()
            self.report = self.report.append(pd.DataFrame({
                'rid': [rid],
                'rid_ch_name': [rid_ch_name],
                'runs_count': [runs_count],
                'avg_run_stop_rate': [avg_run_stop_rate],
            }), ignore_index=True)

        station_center.disconnect()

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)

    def view_in_html(self):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")
        df_for_user = parsing_df_for_user(self.report)
        template_vars = {
            "title": self.title,
            "vid_ch_name": self.vid_ch_name,
            "start_date": self.start_time.strftime("%Y-%m-%d"),
            "end_date": self.end_time.strftime("%Y-%m-%d"),
            "report": df_for_user.to_html(),
        }
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("reports/templates/reports/vendor_route_on_time_rate_report_template.html")
        html_out = template.render(template_vars)

        return html_out

    def save_as_pdf(self, over_write: bool = False):
        if not isinstance(self.report, pd.DataFrame):
            raise ValueError("report un define")
        dir_name = "bucket/" + self.title + "/" + self.start_time.strftime("%Y-%m-%d")
        file_name = self.vid_ch_name + ".pdf"

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
