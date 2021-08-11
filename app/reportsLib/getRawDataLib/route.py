import os

from .drive_log_db import DriveLogDB
from .station_center import StationCenter
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

logger = logging.getLogger()
load_dotenv()

TIME_SHIFT = int(os.getenv("TIME_SHIFT"))

class Route:
    def __init__(self, rid: int, MongoDBOptions: dict, sqlOption: dict):
        self.rid = rid
        self.station_center = StationCenter(sqlOption=sqlOption)
        self.drive_log_db = DriveLogDB(MongoDBOptions=MongoDBOptions)
        self.vid = None
        self.vid_ch_name = None

    def connect(self):
        self.station_center.connect()
        self.drive_log_db.connect()

    def disconnect(self):
        self.station_center.disconnect()
        self.drive_log_db.disconnect()

    def get_ch_name(self):
        return self.station_center.get_route_ch_name(rid=self.rid)

    def get_eng_name(self):
        return self.station_center.get_route_eng_name(rid=self.rid)

    def get_vid(self):
        try:
            self.vid = self.station_center.get_route_vid(rid=self.rid)
            return self.vid
        except Exception as err:
            logger.error(f"cant find vid by rid= {self.rid}")
            return None

    def get_vid_ch_name(self):
        if self.vid is None:
            self.get_vid()
        try:
            self.vid_ch_name = self.station_center.get_vid_ch_name(vid=self.vid)
            return self.vid_ch_name
        except Exception as err:
            logger.error(f"cant find vid_ch_name by vid= {self.vid}")
            return None

    def get_schedule(self, start_time: datetime, end_time: datetime = None):
        return self.station_center.get_schedule_by_rid(rid=self.rid, start_time=start_time, end_time=end_time)

    def get_first_stop_name(self):
        return self.station_center.get_first_stop_name(rid=self.rid)

    def get_first_stop_sid(self):
        return self.station_center.get_first_stop_sid(rid=self.rid)

    def get_stops_name(self):
        return self.station_center.get_route_stops_name(rid=self.rid)

    def get_departure_log_by_sid(self, start_time: datetime, sid: int, end_time: datetime = None):
        if end_time is None:
            end_time = start_time
        elif start_time > end_time:
            raise ValueError("start_time should be earlyer than end_time")
        logs = pd.DataFrame()
        mongo_cmd = {"$and": [{'rid': self.rid},
                              {"event": "StopEnterLeave"},
                              {"type": 0},
                              {"station": sid}]}
        while start_time <= end_time:  # get data from different days collection
            logs = logs.append(self.drive_log_db._get_drive_logs(start_time, mongo_cmd), ignore_index=True)
            start_time = start_time + pd.Timedelta(timedelta(days=1))

        if logs.empty:
            return logs

        logs = pd.DataFrame({'date': logs['date'],  # make logs shorter
                             'did': logs['did'],
                             'cid': logs['cid'],
                             'carno': logs['carno'],
                             'date_gps': logs['date_gps'],
                             'sne': logs['sne']
                             })
        return logs
