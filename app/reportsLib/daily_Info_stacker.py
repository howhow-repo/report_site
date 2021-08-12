from datetime import datetime, timedelta
import sys, traceback
import pandas as pd
import logging
from .getRawDataLib import Bus
from .getRawDataLib import StationCenter, MongoDB
from .getRawDataLib.error_codes import RunlogsTaskErrorCode


logger = logging.getLogger()


def days_in_list(start_date: datetime, end_date: datetime = None):
    if end_date is None:
        return [start_date]
    assert end_date >= start_date
    days = []
    t = start_date
    while t <= end_date:
        days.append(t)
        t = t + timedelta(days=1)
    return days


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
        self.total_runs = pd.DataFrame({})
        self.total_stop_to_stop = pd.DataFrame({})
        self.drove_bus = []
        self.exception_bus = []
        self.error = RunlogsTaskErrorCode()
        self.error_message = []
        self.time_spent = 0
        self.result = {
            'date': [],
            'bus_count': len(self.drove_bus),
            'runs_count': len(self.total_runs),
            'stoptostop_count': len(self.total_stop_to_stop),
            'exception_bus_count': len(self.exception_bus),
            'time_spent': self.time_spent,
            'exception_buses': self.exception_bus,
            'error_message': [],
            'error_code': self.error.error_code,
        }
    def refresh_result(self):
        self.result['bus_count'] = len(self.drove_bus)
        self.result['runs_count'] = len(self.total_runs)
        self.result['stoptostop_count'] = len(self.total_stop_to_stop)
        self.result['exception_bus_count'] = len(self.exception_bus)
        self.result['time_spent'] = self.time_spent
        self.result['exception_buses'] = self.exception_bus
        self.result['error_message'] = self.error_message
        self.result['error_code'] = self.error.error_code
        return self.result

    def get_drove_bus_list(self, days: list):
        self.__MongoHandler.connect()
        bus_list = []
        for day in days:
            bus_list = bus_list + self.__MongoHandler.get_distinct(day, 'drivelog', {}, 'carno')
        self.__MongoHandler.disconnect()
        self.drove_bus = list(set(bus_list))
        self.drove_bus.sort()

    def gather_run_logs_by_buses(self, bus_list: list, date: datetime):
        date = date - timedelta(hours=date.hour, minutes=date.minute, seconds=date.second,
                                microseconds=date.microsecond)
        self.total_runs = pd.DataFrame({})
        self.total_stop_to_stop = pd.DataFrame({})
        self.exception_bus = []
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
                    self.total_runs = self.total_runs.append(run.df_for_sql(), ignore_index=True)
                    self.total_stop_to_stop = self.total_stop_to_stop.append((run.stop_to_stop_df))
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
                self.exception_bus.append(bus_no)
                continue

            except KeyboardInterrupt:
                logger.warning("key interrupted, stop processing")
                raise KeyboardInterrupt

        bus.disconnect()
        return self.total_runs

    def stack_to_sql(self, redo: bool = False, date: datetime = None):
        self.__station_center.connect()
        if redo:
            self.__station_center.delete_runlogs_by_date(date)
        self.__station_center.insert_data(table_name='runlogs', data=self.total_runs)
        if redo:
            self.__station_center.delete_stoptostop_by_date(date)
        self.__station_center.insert_data(table_name='stoptostop', data=self.total_stop_to_stop)
        self.__station_center.disconnect()

    def start(self, start_date: datetime, end_date: datetime = None, redo: bool = False):
        time_started = datetime.now()
        if end_date is None:
            end_date = start_date
        else:
            assert end_date >= start_date

        days = days_in_list(start_date, end_date)

        try:
            self.get_drove_bus_list(days)
        except Exception:
            print(Exception)
            self.error_message.append("SOMETHING WENT WRONG WHILE GETTING DRIVELOG FROM MONGODB")
            self.error.add_error('MONGODBERROR')
            self.time_spent = int((datetime.now() - time_started).seconds)
            return self.refresh_result()

        # calculate
        for day in days:
            #  gather_run_logs
            try:
                print(f"Processing date: {day.strftime('%Y-%m-%d')}")
                print(f'There r {len(self.drove_bus)} buses to check')
                self.gather_run_logs_by_buses(bus_list=self.drove_bus, date=day)
            except Exception:
                print(Exception)
                self.error_message.append("SOMETHING WENT WRONG WHILE GATHERING RUN LOGS")
                self.error.add_error('RUNLOGSCALCULATEERROR')
                self.time_spent = int((datetime.now() - time_started).seconds)
                return self.refresh_result()

            # save to sql
            try:
                print('Saving data to sql ... ')
                self.stack_to_sql(redo=redo, date=day)
                print('Saving success')
            except Exception:
                print(Exception)
                self.error_message.append("SOMETHING WENT WRONG WHILE SAVING RUN LOGS")
                self.error.add_error('MYSQLSAVINGERROR')
                self.time_spent = int((datetime.now() - time_started).seconds)
                raise Exception
                # return self.refresh_result()

        self.time_spent = int((datetime.now() - time_started).seconds)
        print(f'----Time spent: {datetime.now() - time_started} ----')

        if len(self.exception_bus) != 0:
            print(f"err bus = {self.exception_bus}, \n please check manually.")

        self.result['date'] = days
        return self.refresh_result()
