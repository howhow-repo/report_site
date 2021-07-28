import pandas as pd

from .drive_log_db import *
from datetime import datetime,timedelta


class VehicleRecorder(DriveLogDB):
    def __init__(self, ebusMongoDBPath: dict, vid: int):
        super().__init__(ebusMongoDBPath)
        self.vid = vid

    def get_drive_logs(self, datetime: datetime):
        return self._get_drive_logs(datetime, {'vid': self.vid})

    def get_event_logs(self, datetime: datetime, event: str = "StopEnterLeave", type: int = None):
        mongo_cmd = {"$and": [{'vid': self.vid}, {"event": event}]}
        if type is not None:
            mongo_cmd["$and"].append({"type": type})

        return self._get_drive_logs(datetime, mongo_cmd)

    def get_leave_stop(self, start_time: datetime,stop_name: str,end_time: datetime = None):
        if end_time is None:
            end_time = start_time
        elif start_time > end_time:
            raise ValueError("start_time should be earlyer than end_time")

        datetime = start_time
        logs = pd.DataFrame()
        mongo_cmd = {"$and": [{'vid': self.vid},
                              {"event": "StopEnterLeave"},
                              {"type": 0},
                              {"sne": stop_name}]}
        while datetime <= end_time:
            logs = logs.append(self._get_drive_logs(datetime, mongo_cmd))
            datetime = datetime + pd.Timedelta(timedelta(days=1))

        return logs

    def get_enter_stop(self, datetime: datetime, stop_name: str):
        mongo_cmd = {"$and": [{'vid': self.vid},
                              {"event": "StopEnterLeave"},
                              {"type": 1},
                              {"sne": stop_name}]}

        return self._get_drive_logs(datetime, mongo_cmd)
