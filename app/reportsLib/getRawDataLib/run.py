import pandas as pd
from datetime import datetime
from itertools import groupby
from .error_codes import RunErrorCode
import logging
from .stop_to_stop import StopToStop
from datetime import timedelta

logger = logging.getLogger(__name__)


def nearest_time_index(date: datetime, schedule: pd.DataFrame) -> int:
    """ Return the index of schedule where schedule['starttime'] is abs nearest to date """
    nearest_index = None
    min_timedelta = None
    for i, time in enumerate(schedule['starttime']):
        temp = abs(time - date)
        if (min_timedelta is None) or (min_timedelta >= temp):
            nearest_index = i
            min_timedelta = temp
    return nearest_index


class Run:
    """
        泛指一趟出車，出車紀錄的各項指標。
        Attributes:{
            'logs': '此趟車的原始紀錄樣本',
            'carno': '車牌號碼',
            'cid':'車輛id',
            'did':'駕駛員id',
            'vid':'營運商id',
            'rid':'路線id',
            'dutystatus':'值勤狀態',
            weekdayType:'紀錄當天為平日假日等',
            rid_ch_name:'路線中文名稱',
            route_stops:'路線預計經過站牌list',
            route_stops_count:'路線預計經過站牌數',
            bus_departure_time:'實際發車時間',
            bus_departure_stop:'實際發車站id',
            bus_departure_sne:'實際發車站名',
            bus_arrival_time:'實際到達終點站時間',
            bus_arrival_stop:'實際到達最後一站id',
            bus_arrival_sne:'實際到達最後一站站名',
            traveled_stops:'實際經過的站list',
            traveled_stops_count:'實際經過的站數量',
            run_stop_rate:'到站率(應到達站中有實際到達的站數 / 應到達站數)(若紀錄有不在應到站中，即不計算在到站率)',

            schedule_id:'對應到sql中schedule表id (若實際發車時間+-20分鐘內無班次可對應，則為None)',
            schedule_departure_time:'預計發車時間；無schedule_id則為None',
            departure_timedelta:'實際發車時間與表定發車時間差(秒)；正數為比預計時間晚發車；複數為比預計時間早發車',
            stop_to_stop_list = [] 存入此Run經過的 class StopToStop
            stop_to_stop_df = 將此班車的站到站資訊整合而成的dataframe
            erroe_code:各式異常，以每個bit紀錄之{
                'NOSCHEDULETODAY': 1,  # 當日schedule中無此路線
                'OUTOFSCHEDULERANGE': 2,  # 不在班次時間範圍內
                'NEVERARRIVED': 4,  # 當日紀錄無進站紀錄
                'TOOFEWSTOPTRAVELED': 8,  # 實際行駛站數<應行駛站數
                'TOOMANYSTOPTRAVELED': 16,  # 實際行駛站數>應行駛站數
                'NOTFROMFIRSTSTOP': 32,  # 未從首站出發
                'NOTARRIVETOLASTSTOP': 64,  # 未到達終點站
                'STATIONUNDEFINED': 128,  # 路途上有無法辨識sid
                'UNKNOWNERROR': 256,
                'CANNOTFINDROUTESTOPS': 512,  # sql中查不到此路線順序
                'CANNOTFINDFIRSTDEPARTURE': 1024,  # 車輛紀錄有進起始站，卻未出起始站,
            }
        }

    """

    def __init__(self, run_logs: pd.DataFrame, route_ch_name=None,
                 route_stops: pd.DataFrame = pd.DataFrame({}), route_schedule=None, weekdayType=None,
                 run_error_code: RunErrorCode = None):
        if run_error_code is not None:
            self.error = run_error_code
        else:
            self.error = RunErrorCode()
        self.long_stay_logs = pd.DataFrame({})
        self.logs = run_logs
        self.carno = run_logs['carno'].iloc[0]
        self.cid = run_logs['cid'].iloc[0]
        self.vid = run_logs['vid'].iloc[0]
        self.did = run_logs['did'].iloc[0]
        self.rid = run_logs['rid'].iloc[0]
        dutystatusCounts = run_logs.loc[:, 'dutystatus'].value_counts()  # 统计dutystatus數量
        mostDutystatus = dutystatusCounts.idxmax()  # 找出dutystatus最多的數量
        self.dutystatus = mostDutystatus
        self.rid_ch_name = route_ch_name
        self.route_stops = route_stops['rsid'].tolist()
        self.route_stops_count = len(route_stops)
        self.traveled_stops = [i[0] for i in groupby(run_logs['station'])]
        if any((elem < 0) for elem in self.traveled_stops):
            self.error.add_error('STATIONUNDEFINED')
        self.traveled_stops_count = len([i[0] for i in groupby(run_logs['station'])])
        self.schedule_id = None
        self.schedule_departure_time = None
        self.departure_timedelta = None

        # 找第一個站 and 第一個站的發車紀錄
        first_rsid = self.traveled_stops[0]
        first_departure_index = run_logs[(run_logs['station'] == first_rsid)].where(
            run_logs['type'] == 0).last_valid_index()

        if first_departure_index is not None:
            self.bus_departure_time = run_logs['date_gps'].iloc[first_departure_index]
            self.bus_departure_stop = run_logs['station'].iloc[first_departure_index]
            self.bus_departure_sne = run_logs['sne'].iloc[first_departure_index]
        else:
            # 若第一個站沒有發車紀錄，紀錄為異常
            self.error.add_error('CANNOTFINDFIRSTDEPARTURE')

            # 存入無出站資料的站名＆站rsid, 作為起始
            first_departure_index = run_logs[(run_logs['station'] == first_rsid)].where(
                run_logs['type'] == 1).last_valid_index()
            self.bus_departure_stop = run_logs['station'].iloc[first_departure_index]
            self.bus_departure_sne = run_logs['sne'].iloc[first_departure_index]

            try:  # 往下找出距離最近的紀錄時間, 當作發車時間
                next_departure_index = run_logs[(run_logs['station'] != first_rsid)].first_valid_index()
                self.bus_departure_time = run_logs['date_gps'].iloc[next_departure_index]
            except TypeError:  # 若往下皆無出站紀錄，以第一筆進站作為departure_time
                self.error.add_error('UNKNOWNERROR')
                first_arrival_index = run_logs[(run_logs['station'] == first_rsid)].where(
                    run_logs['type'] == 1).first_valid_index()
                self.bus_departure_time = run_logs['date_gps'].iloc[first_arrival_index]

        # 找最後一筆進站紀錄
        last_arrival_index = (
            run_logs[run_logs['event'] == 'StopEnterLeave'].where(run_logs['type'] == 1)
        ).last_valid_index()
        if last_arrival_index is not None:
            self.bus_arrival_time = run_logs['date_gps'].iloc[last_arrival_index]
            self.bus_arrival_stop = run_logs['station'].iloc[last_arrival_index]
            self.bus_arrival_sne = run_logs['sne'].iloc[last_arrival_index]
        else:
            self.error.add_error("NEVERARRIVED")
            self.bus_arrival_time = None
            self.bus_arrival_stop = None
            self.bus_arrival_sne = None

        # 以路線與紀錄比較，計算到站率
        if len(self.route_stops) > 0:
            if self.bus_departure_stop != self.route_stops[0]:
                self.error.add_error('NOTFROMFIRSTSTOP')
            if self.route_stops[-1] not in self.traveled_stops: # 歷程中有到終點站，及算有到達站
                self.error.add_error('NOTARRIVETOLASTSTOP')
            stop_len_in_route = len(set(self.route_stops) - (set(self.route_stops) - set(self.traveled_stops)))
            self.run_stop_rate = stop_len_in_route / self.route_stops_count
        else:
            logger.warning(f'cant find route stops from rid: {self.rid}')
            self.error.add_error('CANNOTFINDROUTESTOPS')
            self.run_stop_rate = 1

        if self.run_stop_rate > 1:
            self.error.add_error('TOOMANYSTOPTRAVELED')
        elif self.run_stop_rate < 1:
            self.error.add_error('TOOFEWSTOPTRAVELED')

        # 計算所屬班次
        if route_schedule.empty:
            # logger.warning(f'run is not in schedule, cant find schedle of {self.rid} today')
            self.departure_timedelta = 0
            self.error.add_error('NOSCHEDULETODAY')
        else:
            if self.bus_departure_time is not None:
                run_time_index = nearest_time_index(self.bus_departure_time, route_schedule)
                self.schedule_id = route_schedule['id'][run_time_index]
                self.schedule_departure_time = route_schedule['starttime'][run_time_index]
                self.departure_timedelta = int((self.bus_departure_time - self.schedule_departure_time).total_seconds())
                if abs(self.departure_timedelta) > 1200:  # 與最近的時程差20分鐘以上，則不算該班次
                    self.schedule_id = None
                    self.schedule_departure_time = None
                    self.error.add_error('OUTOFSCHEDULERANGE')

        self.weekdayType = weekdayType
        self.stop_to_stop_list = []
        self.stop_to_stop_df = pd.DataFrame({})
        self.to_dataframe()

    def to_dataframe(self):
        self.df = pd.DataFrame({
            'carno': [self.carno],
            'cid': [self.cid],
            'vid': [self.vid],
            'did': [self.did],
            'rid': [self.rid],
            'rid_ch_name': [self.rid_ch_name],
            'dutystatus': [self.dutystatus],
            'bus_departure_time': [self.bus_departure_time],
            'bus_departure_stop': [self.bus_departure_stop],
            'bus_departure_sne': [self.bus_departure_sne],
            'bus_arrival_time': [self.bus_arrival_time],
            'bus_arrival_stop': [self.bus_arrival_stop],
            'bus_arrival_sne': [self.bus_arrival_sne],
            'traveled_stops_count': [self.traveled_stops_count],
            'route_stops_count': [self.route_stops_count],
            'run_stop_rate': [self.run_stop_rate],
            'schedule_id': [self.schedule_id],
            'schedule_departure_time': [self.schedule_departure_time],
            'departure_timedelta': [self.departure_timedelta],
            'weekdayType': [self.weekdayType],
            'error_code': [self.error.error_code]
        })
        return self.df

    def df_for_sql(self):
        df = self.to_dataframe().copy()
        del df['rid_ch_name']
        del df['bus_departure_sne']
        del df['bus_arrival_sne']
        return df

    def stop_to_stop_statistics(self):
        df = pd.DataFrame(columns=['carno','rsid', 'previous_rsid', 'next_rsid', 'isFirst', 'isLast',
                                   'arrival_time', 'departure_time', 'stay_time', 'arrival_time_spent',
                                   'error_code'])
        previous_stop_info = None
        for i, stop in enumerate(self.traveled_stops):  # 跑過實際跑過的站
            one_stop_log = self.logs.loc[self.logs[(self.logs['station'] == stop)].index].copy()
            try:
                if stop == self.traveled_stops[-1]:
                    next_rsid = None
                else:
                    index_stop_in_route = self.route_stops.index(stop)
                    if index_stop_in_route < len(self.route_stops)-1:
                        next_rsid = self.route_stops[index_stop_in_route+1]
                    else:
                        next_rsid = None
            except ValueError:
                next_rsid = None

            s = StopToStop(logs=one_stop_log.reset_index(), previous_stop_info=previous_stop_info, next_rsid=next_rsid)
            s.weekdayType = self.weekdayType

            # check long stay
            if not self.long_stay_logs.empty:
                # check if long stay between stops
                if (previous_stop_info is not None) and (previous_stop_info.departure_time is not None) and (s.arrival_time is not None):
                    filtered_long_stay = self.long_stay_logs.loc[
                        (self.long_stay_logs['date_gps'] > previous_stop_info.departure_time)
                        & (self.long_stay_logs['date_gps'] < s.arrival_time)
                    ]
                    if not filtered_long_stay.empty:
                        s.error_code.add_error('LONGSTAYBETWEENSTOP')

                # check longstay in stop
                if (s.arrival_time is not None) and (s.departure_time is not None):
                    filtered_long_stay = self.long_stay_logs.loc[
                        (self.long_stay_logs['date_gps'] > s.arrival_time)
                        & (self.long_stay_logs['date_gps'] < s.departure_time)]
                    if not filtered_long_stay.empty:
                        s.error_code.add_error('LONGSTAYINSTOP')

            self.stop_to_stop_list.append(s)

            df = df.append(self.stop_to_stop_list[-1].to_dataframe(),ignore_index=True)
            previous_stop_info = self.stop_to_stop_list[-1]
        df['carno'] = self.carno
        self.stop_to_stop_df = df

