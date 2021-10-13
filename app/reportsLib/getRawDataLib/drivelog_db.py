# coding=utf-8
import os

from datetime import datetime, timedelta
import pandas as pd
import logging
from dotenv import load_dotenv
from .mongo_db_handler import MongoDB

load_dotenv()
logger = logging.getLogger(__name__)
time_shift = int(os.getenv("TIME_SHIFT"))


class DriveLogDB(MongoDB):
    def __init__(self, MongoDBOptions: dict, DBName: str = 'ebus'):
        super().__init__(MongoDBOptions, DBName)

    def get_rids(self, datetime: datetime):
        return sorted(self.get_distinct(datetime=datetime, collection_type='drivelog',
                                        query_cmd={"event": "StopEnterLeave"},
                                        field_name='rid'))

    def get_drove_buses(self, datetime: datetime):
        datetime = datetime.replace(hour=0, minute=0, second=0)
        bus_list = self.get_distinct(datetime, 'drivelog', {}, 'carno')
        bus_list = bus_list + (self.get_distinct(datetime + timedelta(days=1), 'drivelog',
                                       {
                                            "date_gps": {
                                                "$lt": datetime+timedelta(days=1, hours=time_shift)
                                            }
                                       }, 'carno'))
        drove_buses = list(set(bus_list))
        return drove_buses

    def _get_drive_logs(self, datetime: datetime, query_cmd: dict, projection_cmd: dict = None):
        datetime = datetime.replace(hour=0, minute=0, second=0)
        logs = self._get_logs(datetime=datetime, collection_type='drivelog', query_cmd=query_cmd,
                              projection_cmd=projection_cmd)
        logs = logs.append(
            self._get_logs(datetime=datetime + timedelta(days=1), collection_type='drivelog', query_cmd=query_cmd,
                           projection_cmd=projection_cmd), ignore_index=True)
        if logs.empty:
            return logs

        logs['date_gps'] = pd.to_datetime(logs['date_gps'])
        mask = (logs['date_gps'] > datetime + timedelta(hours=time_shift)) & (
                logs['date_gps'] <= datetime + timedelta(days=1, hours=time_shift))
        logs = logs.loc[mask]
        return logs
