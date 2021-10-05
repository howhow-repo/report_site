import os

import numpy as np

from .report_base import ReportBase
from datetime import datetime, timedelta
from .getRawDataLib import StationCenter
import pdfkit
import pandas as pd
from jinja2 import Environment, FileSystemLoader


def parsing_df_for_user(report: pd.DataFrame):
    if report.empty:
        return pd.DataFrame(columns=['表定發車時間', '總發車數量', '準時出車數量', '脫班車數量', '首站發車(Y/N)'])

    main_report = report.copy()  # 開始處裡準點報表

    main_report = main_report[
        ['starttime', 'bus_count', 'on_time_bus_count', 'not_on_time_bus_count', 'from_first_stop']
    ]
    main_report['from_first_stop'] = main_report['from_first_stop'].replace([True, False, None], ['Y', 'N', ''])

    main_report.replace([np.nan, None, "nan%"], '', inplace=True)

    main_report.rename(columns={'starttime': '表定發車時間',
                                'bus_count': '總發車數量',
                                'on_time_bus_count': '準時出車數量',
                                'not_on_time_bus_count': '脫班車數量',
                                'from_first_stop': '首站發車(Y/N)'
                                }, inplace=True)
    main_report.index += 1  # index from 1
    return main_report


class RouteScheduleDepartureCountReport(ReportBase):
    """
        以路線班次為基準，計算各班次有多少車，發車是否為準時。
        預設+-20min中即不算漏班;預設準點時間為早 1 min~晚 5 min

        report schema:{
            'schedule_id': '每個班次會有自己的uid',
            'starttime': '班次的表定發車時間',
            'bus_count': '此班次總發車數量',
            'on_time_bus_count': '此班次發車數量中，準點發車的數量',
            'not_on_time_bus_count': '此班次發車數量中，非準點發車的數量',
            'early_bus_count': '此班次非準點發車的數量中，過早發車的數量',
            'delay_bus_count': '此班次非準點發車的數量中，過晚發車的數量',
            'from_first_stop': '此班次發車數量中，非從起始站發車的數量',
        }
        * bus_count = on_time_bus_count + not_on_time_bus_count
        * not_on_time_bus_count = early_bus_count + delay_bus_count
        * from_first_stop: 純粹看發車位置，與發車時間無關。
    """
    title = '路線班次發車次數統計'
    simple_description = '以路線班次為基準，計算各班次有多少車，發車是否為準時。'

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        super().__init__(centerDB_conn_options, drivelogDB_conn_options)
        self.start_time = None
        self.end_time = None
        self.rid = None
        self.rid_name = None
        self.vid = None
        self.vid_ch_name = None

    def generate_report(self, start_time: datetime, rid: int, off_duty_tol: int = 1200,
                        early_tol: int = 60, delay_tol: int = 300, end_time: datetime = None, **kwargs):
        """
        input:
            start_time: 紀錄開始時間，以每日00:00開始計算。
            off_duty_tol: (秒) 若該班車與最接近的發車時間超過此，則為漏班，這趟車就不算在班次中。預設為1200
            early_tol: (秒) 若發車時間早於此秒數，則視為過早發車。預設為60
            delay_tol: (秒) 若發車時間晚於此秒數，則視為過晚發車。預設為300
            end_time: 紀錄結束時間，可不填入，則預設為start_time當天。
        """
        self.start_time = start_time - timedelta(hours=start_time.hour,minutes=start_time.minute,
                                                 seconds=start_time.second,microseconds=start_time.microsecond)
        if end_time is not None:
            assert end_time >= start_time
            self.end_time = end_time
        else:
            self.end_time = start_time

        self.rid = rid

        self.report = pd.DataFrame(columns=['schedule_id', 'starttime', 'bus_count', 'on_time_bus_count',
                                            'not_on_time_bus_count', 'early_bus_count', 'delay_bus_count',
                                            'from_first_stop'])

        station_center = StationCenter(sqlOption=self._centerDB_conn_options)
        station_center.connect()
        self.rid_name = station_center.get_route_ch_name(self.rid)
        self.sub_title = "路線：" + self.rid_name

        self.vid = station_center.get_route_vid(self.rid)
        self.vid_ch_name = station_center.get_vid_ch_name(self.vid)
        departure_logs = station_center.get_rid_schedule_run_logs(rid=self.rid,
                                                                  start_time=self.start_time, end_time=self.end_time,
                                                                  off_duty_timedelta=off_duty_tol)
        station_center.disconnect()

        # some init for self.report
        self.report['starttime'] = departure_logs['starttime'].unique()
        self.report['schedule_id'] = departure_logs['id'].unique()
        self.report['from_first_stop'] = None
        for col in ['bus_count', 'on_time_bus_count', 'not_on_time_bus_count',
                    'early_bus_count', 'delay_bus_count']:
            self.report[col] = 0

        # calculate
        for i in departure_logs.index:
            if not pd.isnull(departure_logs.loc[i, 'bus_departure_time']):  # 若有發車 該schedule計數+1
                index = self.report[self.report['schedule_id'] == departure_logs.iloc[i]['id']].index.values[0]
                self.report.loc[index, 'bus_count'] += 1
                if (int(departure_logs.loc[i, 'error_code']) & 32) \
                        and pd.isnull(self.report.loc[index, 'from_first_stop']):  # check departure from first stop by error code
                    self.report.loc[index, 'from_first_stop'] = False
                else:
                    self.report.loc[index, 'from_first_stop'] = True

                if (0 - early_tol) <= departure_logs.loc[i, 'departure_timedelta'] <= delay_tol:  # 是否準點發車
                    self.report.loc[index, 'on_time_bus_count'] += 1

                else:  # 非準點發車
                    self.report.loc[index, 'not_on_time_bus_count'] += 1
                    if (0 - early_tol) > departure_logs.loc[i, 'departure_timedelta']:
                        self.report.loc[index, 'early_bus_count'] += 1
                    elif departure_logs.loc[i, 'departure_timedelta'] > delay_tol:
                        self.report.loc[index, 'delay_bus_count'] += 1

    def parsing_df_for_user(self):
        return parsing_df_for_user(self.report)
