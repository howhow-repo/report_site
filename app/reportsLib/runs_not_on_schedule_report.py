# coding=utf-8
import pandas as pd
from datetime import datetime, timedelta
from .report_base import ReportBase
from .getRawDataLib import StationCenter
import logging

logger = logging.getLogger()


def parsing_df_for_user(report: pd.DataFrame):
    if report.empty:
        return pd.DataFrame(columns=['路線名稱', '車牌號碼', '發車時間', '發車站名', '終點站到站時間', '終點站站名',
                                     '到站率', '異常原因'])

    main_report = report.copy()  # 開始處裡準點報表
    main_report['run_stop_rate'] = pd.Series(["{0:.1f}%".format(val * 100) for val in main_report['run_stop_rate']],
                                            index=main_report.index)

    main_report.loc[(main_report['error_code'] & 1) != 0, 'error_type'] = '本日查無班次'
    main_report.loc[(main_report['error_code'] & 2) != 0, 'error_type'] = '非班次時間內發車'

    main_report = main_report[
        ['rid', 'rid_name', 'carno', 'bus_departure_time', 'bus_departure_sne',
         'bus_arrival_time', 'bus_arrival_sne', 'run_stop_rate', 'error_type']
    ]

    main_report.rename(columns={'rid_name': '路線名稱',
                                'carno': '車牌號碼',
                                'bus_departure_time': '發車時間',
                                'bus_departure_sne': '發車站名',
                                'bus_arrival_time': '終點站到站時間',
                                'bus_arrival_sne': '終點站站名',
                                'run_stop_rate': '到站率',
                                'error_type': '異常原因'
                                }, inplace=True)
    main_report.index += 1  # index from 1
    return main_report


class RunsNotOnScheduleReport(ReportBase):
    """
        顯示時間內有多少車次是無對應的班次。
        會在此表中的車有兩種情形：
            ＊ 日期中本身無相關班次。
            ＊ 發車時間+-20min內沒有班次能夠去對應
    """
    title = "無對應班次之發車紀錄一覽表"
    simple_description = "顯示時間內有多少車次是無對應的班次。"

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
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

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.report = station_center.get_runs_not_on_schedule(start_time=start_time, end_time=end_time)
        self.report.reset_index()
        station_center.disconnect()

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)
