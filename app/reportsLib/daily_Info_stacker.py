from datetime import datetime, timedelta
import json, sys, traceback
import pandas as pd
import logging
from .getRawDataLib import Bus
from .getRawDataLib import StationCenter, MongoDB

logger = logging.getLogger()


# getting all carno
class DailyInfoStaker:
    '''
        use to calculate everyday logs and seperate them into Runs;
        StopToStop info is also in Runs;


        also save these runs back into sql DB
    '''

    def __init__(self, MongoDBOptions: dict, sqlOption: dict):
        self.__mongoDBOptions = MongoDBOptions
        self.__sqlOption = sqlOption
        self.__station_center = StationCenter(sqlOption=sqlOption)
        self.__MongoHandler = MongoDB(MongoDBOptions=MongoDBOptions)
        self.totle_runs = pd.DataFrame({})
        self.totle_stop_to_stop = pd.DataFrame({})
        self.err_bus = []
        self.error_code = 0

    def gather_run_logs_by_buses(self, bus_list: list, date: datetime):
        date = date - timedelta(hours=date.hour, minutes=date.minute, seconds=date.second,
                                microseconds=date.microsecond)
        self.totle_runs = pd.DataFrame({})
        self.totle_stop_to_stop = pd.DataFrame({})
        self.err_bus = []
        bus = Bus(MongoDBPath=self.__mongoDBOptions, sqlOption=self.__sqlOption)
        bus.connect()
        for i, bus_no in enumerate(bus_list):
            try:
                print(f"Now processing carno {bus_no}, {i + 1}/{len(bus_list)}")
                t = datetime.now()
                bus.carno = bus_no
                bus.setup(date)
                for run in bus.runs:
                    print(f"    THIS Run IS BEGIN FROM {run.bus_departure_sne} at {run.bus_departure_time}")
                    self.totle_runs = self.totle_runs.append(run.df_for_sql(), ignore_index=True)
                    self.totle_stop_to_stop = self.totle_stop_to_stop.append((run.stop_to_stop_df))
                print(f"----Done, time spent: {datetime.now() - t}\n")

            except Exception as e:
                logger.warning(f"Met err while carno = {bus_no}, skip")
                error_class = e.__class__.__name__  # 取得錯誤類型
                detail = e.args[0]  # 取得詳細內容
                cl, exc, tb = sys.exc_info()  # 取得Call Stack
                lastCallStack = traceback.extract_tb(tb)  # 取得Call Stack的最後一筆資料
                fileName = lastCallStack[0]  # 取得發生的檔案名稱
                lineNum = lastCallStack[1]  # 取得發生的行號
                funcName = lastCallStack[2]  # 取得發生的函數名稱
                errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
                logger.warning(errMsg)
                self.err_bus.append(bus_no)
                continue

            except KeyboardInterrupt:
                logger.warning("key interrupted, stop processing")
                raise KeyboardInterrupt

        bus.disconnect()
        return self.totle_runs

    def stack_to_sql(self):
        self.__station_center.connect()
        self.__station_center.insert_data(table_name='runlogs', data=self.totle_runs)
        self.__station_center.insert_data(table_name='stoptostop', data=self.totle_stop_to_stop)
        self.__station_center.disconnect()

    def start(self, start_date: datetime, end_date:datetime = None):
        time_started = datetime.now()
        if end_date is None:
            end_date = start_date
        else:
            assert end_date >= start_date

        days = []
        t = start_date
        while t <= end_date:
            days.append(t)
            t = t + timedelta(days = 1)

        for day in days:
            # get_bus_list
            bus_list = []
            self.__MongoHandler.connect()
            bus_list = bus_list + self.__MongoHandler.get_distinct(day, 'drivelog', {}, 'carno')
            self.__MongoHandler.disconnect()
            self.drove_bus = list(set(bus_list))
            self.drove_bus.sort()

            #  gather_run_logs
            print(f"Processing date: {day.strftime('%Y-%m-%d')}")
            print(f'There r {len(self.drove_bus)} buses to check')
            self.gather_run_logs_by_buses(bus_list=self.drove_bus, date=day)

            # save to sql
            while True:
                try:
                    print('Saving data to sql ... ')
                    self.stack_to_sql()
                    print('Saving success')
                    break
                except Exception as e:
                    logger.error(e)
                    k = input('Enter c to retry; press any key to skip sql stack.')
                    if k != 'c':
                        print('system skip')
                        break

        print(f'----Time spent: {datetime.now() - time_started} ----')
        if len(self.err_bus) != 0:
            print(f"err bus = {self.err_bus}, \n please check manually.")
