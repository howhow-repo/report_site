import pandas as pd
from .error_codes import StopToStopErrorCode


class StopToStop:
    """
    站到站之間的資訊。每個與StopEnterLeave相關的站紀錄皆有一筆
    Attributes:{
            'logs': '與此站相關的原始紀錄樣本',
            'rid':'路線id',
            'rsid':'此站的路線順序id',
            'sne':'此站中文站名',
            previous_rsid:'實際上一站的rsid',
            next_rsid:'預期中會去的下一站rsid',
            isFirst:'是否為實際發車站',
            isLast:'是否為實際終點站',
            arrival_time:'實際到達此站的時間, 起始站為None',
            departure_time:'實際離開此站的時間, 終點站為None',
            stay_time:'此站逗留時間',
            arrival_time_spent:'由上一站到此站實際花費時間',
            weekdayType:'紀錄當天為平日假日等',

            erroe_code:各式異常，以每個bit紀錄之{
                'NOARRIVAL': 1,  # 此站紀錄無進站
                'NODEPARTURE': 2,  # 此戰紀錄無出站
                'TOOMANYLOGS': 4,  # 進出站紀錄連續不只一筆
                'NOTFROMROUTELASTSTOP':8,  # 前一站不如預期
                'NOTENOUGHPREVIOUSDATA':16,  # 前一站資料不足
                'LONGSTAYINSTOP': 32,  # 在站內有longstay紀錄
                'LONGSTAYBETWEENSTOP': 64, # 從上一站過來的路上有longstay紀錄
            }
        }
    """
    def __init__(self, logs:pd.DataFrame, previous_stop_info = None, next_rsid = None,
                 error_code: StopToStopErrorCode = None):
        if error_code is not None:
            self.error_code = error_code
        else:
            self.error_code = StopToStopErrorCode()

        self.logs = logs
        self.rid = self.logs.loc[0, 'rid']
        self.rsid = self.logs.loc[0, 'station']
        self.sne = self.logs.loc[0, 'sne']
        self.previous_rsid = None
        if previous_stop_info is not None:
            self.previous_rsid = previous_stop_info.rsid
            if previous_stop_info.next_rsid != self.rsid:
                self.error_code.add_error("NOTFROMROUTELASTSTOP")

        self.next_rsid = next_rsid

        self.isFirst = False
        self.isLast = False

        self.arrival_time = None
        self.departure_time = None
        self.stay_time = None
        self.arrival_time_spent = None
        self.weekdayType = None

        if len(logs[(logs['type'] == 0)].index)>0: # 找出站紀錄
            type0_index = logs[(logs['type'] == 0)].index[-1]
        else:
            type0_index = logs[(logs['type'] == 1)].index[-1]
            if next_rsid is not None:  # 非終點站
                self.error_code.add_error('NODEPARTURE')

        if len(logs[(logs['type'] == 1)].index) > 0: # 找進站紀錄
            type1_index = logs[(logs['type'] == 1)].index[0]
        else:
            type1_index = logs[(logs['type'] == 0)].index[0]
            if previous_stop_info is not None:  # 非起始站
                self.error_code.add_error('NOARRIVAL')


        if previous_stop_info is None:  # 起始站
            self.isFirst = True
            self.departure_time = logs['date_gps'].loc[type0_index]

        elif next_rsid is None:  #  終點站
            self.isLast = True
            self.arrival_time = logs['date_gps'].loc[type1_index]
            if previous_stop_info.departure_time is not None:
                self.arrival_time_spent = int((self.arrival_time - previous_stop_info.departure_time).total_seconds())
            else:
                self.arrival_time_spent = None
                self.error_code.add_error('NOTENOUGHPREVIOUSDATA')

        else: # 一般站
            self.departure_time = logs['date_gps'].loc[type0_index]
            self.arrival_time = logs['date_gps'].loc[type1_index]
            self.stay_time = int((self.departure_time - self.arrival_time).total_seconds())
            if previous_stop_info.departure_time is not None:
                self.arrival_time_spent = int((self.arrival_time - previous_stop_info.departure_time).total_seconds())
            else:
                self.arrival_time_spent = None
                self.error_code.add_error('NOTENOUGHPREVIOUSDATA')

    def to_dataframe(self):
        self.df = pd.DataFrame({'rid':[self.rid],
                                'rsid':[self.rsid],
                                'previous_rsid':[self.previous_rsid],
                                'next_rsid':[self.next_rsid],
                                'isFirst':[self.isFirst],
                                'isLast':[self.isLast],
                                'arrival_time':[self.arrival_time],
                                'departure_time':[self.departure_time],
                                'stay_time':[self.stay_time],
                                'arrival_time_spent':[self.arrival_time_spent],
                                'weekdayType':[self.weekdayType],
                                'error_code':[self.error_code.error_code]})
        return self.df
