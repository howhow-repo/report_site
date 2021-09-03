from .drive_log_db import *
from .station_center import StationCenter
from .run import Run


def split_logs_by_rid(bus_logs: pd.DataFrame) -> list:  # return a list of Dataframe
    head_pointer = 0
    end_pointer = head_pointer
    runs = []
    while (bus_logs.index == head_pointer).any():  # 當headerpointer指的到值時
        run = pd.DataFrame()
        now_rid = bus_logs['rid'].iloc[end_pointer]
        if pd.isnull(now_rid):  # 若log中沒有rid資訊，即指向下一筆
            head_pointer += 1
            continue

        for log in bus_logs['rid'][head_pointer:]:
            if log == now_rid:
                head_pointer += 1
            else:
                break
        run = run.append(bus_logs.iloc[end_pointer:head_pointer], ignore_index=True)
        end_pointer = head_pointer
        runs.append(run.copy())
        del run

    return runs


def split_logs_by_route_stop_sequence(logs: pd.DataFrame, schedule: pd.DataFrame) -> list:
    logs.sort_values(by=['date_gps', 'date'], inplace=True, ignore_index=True)
    list_of_log = []
    head_pointer = 0
    end_pointer = head_pointer
    checking_index = 0
    for station in logs['station']:  # 跑過全部的drive log
        not_yet_ran_schedule = schedule.iloc[checking_index:]['rsid'].tolist()  # 尚未開過的車站=需被檢查的車站
        if station in not_yet_ran_schedule:  # 若drivelog該站為 尚未開過的站
            checking_index = schedule[schedule['rsid'] == station].index.values[0]  # 找出目前的drive log屬於第幾站
        else:  # 若drivelog該站 在後續的站中找不到
            if station in schedule.iloc[:checking_index]['rsid'].tolist():  # 該站有在前面開過的站 就當作回頭了
                ran_log = logs.iloc[end_pointer:head_pointer]
                ran_log.reset_index(inplace=True)
                list_of_log.append(ran_log)  # 將前面走過的log存成一包;把這包log推進return用的list
                end_pointer = head_pointer  # 重新位置開始計drive log
                checking_index = schedule[schedule['rsid'] == station].index.values[0]  # 找出目前的drive log屬於第幾站
            elif station < 0:  # 該站sid = -1 則dont care
                head_pointer += 1  # 指標指向drivelog下一站
                continue
            # TODO: other situation handling

        head_pointer += 1  # 指標指向drivelog下一站

    ran_log = logs.iloc[end_pointer:head_pointer]
    ran_log.reset_index(inplace=True)
    list_of_log.append(ran_log)

    return list_of_log


class Bus(DriveLogDB):
    """
        每一輛公車即可用該車牌init起來。
        Warining! Bus init起來依然是空的，需要連線與撈取logs回來才能開始計算各項Attributes。


        use case:
            bus = Bus(MongoDBPath=mongo_options,sqlOption=sql_options,carno="KKA-8692")
            bus.connect()
            bus.setup(start_time=datetime(2021, 7, 17),end_time=datetime(2021, 7, 18))
            bus.disconnect()

        Attributes:{
            'travel_logs': '此公車在setup時間內全部的原始紀錄資料樣本',
            'carno': '車牌號碼',
            'traveled_stops':'實際經過的站牌rsid list',
            'long_stay_logs':'紀錄發生longstay事件與時間的dataframe',
            'runs':'將所有此公車setup時間內所跑的趟次，以class Run的形式存在此list',
            'station_center':'藉由此物件查詢除存在公車總站的sql資訊。',

        }
    """

    def __init__(self, MongoDBPath: dict, sqlOption: dict, carno: str = None):
        super().__init__(MongoDBPath)
        self.carno = carno
        self.travel_logs = pd.DataFrame({})
        self.traveled_stops = []
        self.long_stay_logs = pd.DataFrame({})
        self.runs = []
        self.station_center = StationCenter(sqlOption=sqlOption)

    def connect(self):
        super(Bus, self).connect()
        self.station_center.connect()

    def disconnect(self):
        super(Bus, self).disconnect()
        self.station_center.disconnect()

    def get_travel_logs(self, start_time: datetime, end_time: datetime = None):
        if end_time is None:
            end_time = start_time
        else:
            assert end_time >= start_time
        self.travel_logs = pd.DataFrame({})
        s = start_time
        while s <= end_time:  # get data from different days collection
            one_day_log = self._get_drive_logs(datetime=start_time,
                                               query_cmd={"$and": [{"carno": self.carno}, {"event": "StopEnterLeave"}]},
                                               projection_cmd={"lon": 0, "lat": 0, "gxrid": 0,
                                                               "_id": 0, "severity": 0, "speed": 0,
                                                               "direct": 0,
                                                               "doorOpen": 0, "busstatus": 0})
            self.travel_logs = self.travel_logs.append(one_day_log, ignore_index=True)
            s = s + pd.Timedelta(timedelta(days=1))
        if not self.travel_logs.empty:
            self.travel_logs.sort_values(by=['date_gps'], inplace=True, ignore_index=True)

        self.__get_long_stay_logs(start_time=start_time, end_time=end_time)
        return self.travel_logs

    def __get_long_stay_logs(self, start_time: datetime, end_time: datetime = None):
        if end_time is None:
            end_time = start_time
        else:
            assert end_time >= start_time
        self.long_stay_logs = pd.DataFrame({})
        while start_time <= end_time:
            long_stays = self._get_drive_logs(datetime=start_time,
                                              query_cmd={"$and": [{"carno": self.carno}, {"event": "LongStay"}]},
                                              projection_cmd={"carno": 1, "vid": 1, "did": 1, "cid": 1,
                                                              "dutystatus": 1, "date": 1,
                                                              "date_gps": 1, "event": 1, "busstatus": 1})
            self.long_stay_logs = self.long_stay_logs.append(long_stays, ignore_index=True)
            start_time = start_time + pd.Timedelta(timedelta(days=1))

    def standardize_runs_logs(self):
        if self.travel_logs.empty:
            return 0
        # reset attr
        self.traveled_stops = []
        self.runs = []

        runs = split_logs_by_rid(self.travel_logs)  # 全部的drive log先用rid去切

        for run in runs:  # 把每個切完的rid再拿去跟路線順序比較，若是兩趟以上就再切
            route_stops = self.station_center.get_route_rsid(run['rid'].loc[0])
            route_schedule = self.station_center.get_schedule_by_rid(rid=run['rid'].loc[0],
                                                                     start_time=run['date_gps'].loc[0])
            route_ch_name = self.station_center.get_route_ch_name(rid=run['rid'].loc[0])
            weekdayType = self.station_center.get_weekdayType(run['date_gps'].loc[0].date())
            splited_logs = split_logs_by_route_stop_sequence(run, route_stops)

            for logs in splited_logs:  # 切完一並生成Run,存入
                if not logs.empty and len(logs) > 3:  # 有時會臨時切錯路線，因此log太短就無視

                    r = Run(run_logs=logs, route_ch_name=route_ch_name,
                            route_stops=route_stops, route_schedule=route_schedule,
                            weekdayType=weekdayType)

                    if not self.long_stay_logs.empty:
                        filtered_long_stay = self.long_stay_logs.loc[
                            (self.long_stay_logs['date_gps'] > r.bus_departure_time)
                            & (self.long_stay_logs['date_gps'] < r.bus_arrival_time)]
                        r.long_stay_logs = filtered_long_stay
                    r.stop_to_stop_statistics()  # calculate after long_stay filtered

                    self.runs.append(r)
                    self.traveled_stops = self.traveled_stops + self.runs[-1].traveled_stops

    def setup(self, start_time: datetime, end_time: datetime = None):
        self.travel_logs = pd.DataFrame({})
        self.traveled_stops = []
        self.long_stay_logs = pd.DataFrame({})
        self.runs = []
        self.get_travel_logs(start_time=start_time,end_time=end_time)
        self.standardize_runs_logs()
