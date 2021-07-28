import os
import pandas as pd
import pdfkit
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
from .report_base import ReportBase
from .route_on_time_rate_report import RouteOnTimeRateReport
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

        main_report = main_report[['rid','rid_name','duty_count', 'off_duty', 'not_from_first_stop',
                                   'early_delay', 'on_time_departure', 'on_time_rate']]

        main_report.rename(columns={'rid_name':'路線名稱',
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


class TotleOnTimeRateReport(ReportBase):
    '''
        以個路線準點報表(route_on_time_rate_report_rnBase)為基礎，建立各路線準點率的報表。


    '''

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.title = "準點率一覽表"
        self.start_time = None
        self.end_time = None
        self.totle_rids = []

    def generate_report(self, start_time: datetime, off_duty_tol:int = 1200,early_tol: int = 60,
                        delay_tol: int = 300, end_time: datetime = None, **kwargs):
        proccess_start = datetime.now()
        self.start_time = start_time - timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                 seconds=start_time.second, microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.totle_rids = station_center.get_rid_list_by_date(start_time=start_time, end_time=end_time)
        station_center.disconnect()

        route_on_time_report = RouteOnTimeRateReport(centerDB_conn_options=self._centerDB_conn_options,
                                                   drivelogDB_conn_options=self._drivelogDB_conn_options)

        # calculating
        report = pd.DataFrame({})
        for i, rid in enumerate(self.totle_rids):
            t = datetime.now()
            print(f"gathering {i + 1}/{len(self.totle_rids)} report from rid {rid}...")
            try:
                route_on_time_report.generate_report(rid=rid, start_time=start_time, end_time=end_time,
                                                     off_duty_tol=off_duty_tol,
                                                     early_tol=early_tol, delay_tol=delay_tol)
            except Exception as err:
                logger.warning(f'can not built rid_on_time_report of rid = {rid}')
                logger.warning(err)
                continue

            report_of_one_rid = route_on_time_report.report
            report_of_one_rid['rid'] = route_on_time_report.rid
            report_of_one_rid['rid_name'] = route_on_time_report.rid_name
            report_of_one_rid['vid'] = route_on_time_report.vid
            report_of_one_rid['vid_ch_name'] = route_on_time_report.vid_ch_name
            report = report.append(report_of_one_rid, ignore_index=True)
            print(f"----Done, time spent: {datetime.now() - t}\n")

        self.report = report
        print(f'----Time spent: {datetime.now() - proccess_start} ----')

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
        template = env.get_template("reports/templates/reports/totle_on_time_rate_report_template.html")
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
