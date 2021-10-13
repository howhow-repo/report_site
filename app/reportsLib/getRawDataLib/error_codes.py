# coding=utf-8
import logging

logger = logging.getLogger()

run_err_type = {
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
    'CANNOTFINDFIRSTDEPARTURE': 1024  # 車輛紀錄有進起始站，卻未出起始站
}

stop_to_stop_err_type = {
    'NOARRIVAL': 1,  # 此站紀錄無進站
    'NODEPARTURE': 2,  # 此戰紀錄無出站
    'TOOMANYLOGS': 4,  # 進出站紀錄連續不只一筆
    'NOTFROMROUTELASTSTOP': 8,  # 前一站不如預期
    'NOTENOUGHPREVIOUSDATA': 16,  # 前一站資料不足
    'LONGSTAYINSTOP': 32,  # 在站內有longstay紀錄
    'LONGSTAYBETWEENSTOP': 64,  # 從上一站過來的路上有longstay紀錄
}

runlogs_task_err_type = {
    'MONGODBERROR': 1,
    'RUNLOGSCALCULATEERROR': 2,
    'MYSQLSAVINGERROR': 4
}


class RunErrorCode:
    def __init__(self):
        self.error_code = 0
        self.type_map = run_err_type

    def add_error(self, error_type):
        error = 0
        try:
            error = self.type_map[error_type]
        except Exception as err:
            logger.warning(f"input error type: <{error_type}> is undefined")
        self.error_code = self.error_code | error

    @classmethod
    def print_error_type(cls, error_code):
        err_list = []
        for err in run_err_type.keys():
            if error_code & run_err_type[err] == 1:
                err_list.append(err)
        return err_list


class StopToStopErrorCode:
    def __init__(self):
        self.error_code = 0
        self.type_map = stop_to_stop_err_type

    def add_error(self, error_type):
        error = 0
        try:
            error = self.type_map[error_type]
        except Exception as err:
            logger.warning(f"input error type: <{error_type}> is undefined")
        self.error_code = self.error_code | error

    @classmethod
    def print_error_type(cls, error_code):
        err_list = []
        for err in run_err_type.keys():
            if error_code & run_err_type[err] == 1:
                err_list.append(err)
        return err_list


class RunlogsTaskErrorCode:
    def __init__(self):
        self.error_code = 0
        self.type_map = runlogs_task_err_type

    def add_error(self, error_type):
        error = 0
        try:
            error = self.type_map[error_type]
        except Exception as err:
            logger.warning(f"input error type: <{error_type}> is undefined")
        self.error_code = self.error_code | error

    @classmethod
    def print_error_type(cls, error_code):
        err_list = []
        for err in run_err_type.keys():
            if error_code & run_err_type[err] == 1:
                err_list.append(err)
        return err_list
