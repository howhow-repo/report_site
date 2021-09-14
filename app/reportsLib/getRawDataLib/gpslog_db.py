import os
from datetime import datetime, timedelta

import pandas as pd
import logging
from dotenv import load_dotenv
from .mongo_db_handler import MongoDB

load_dotenv()
logger = logging.getLogger(__name__)


def parsing_hour_cmd(datetime: datetime, hour: int):
    datetime = datetime.replace(hour=hour, minute=0, second=0, microsecond=0)
    return {
        "date_gps": {
            "$gt": datetime,
            "$lte": datetime+timedelta(hours=1)
        }
    }


class GpsLogDB(MongoDB):
    def __init__(self, MongoDBOptions: dict, DBName: str = 'ebus'):
        super().__init__(MongoDBOptions, DBName)

    def get_gpslog_hourly(self, datetime: datetime, hour: int):
        query_cmd = parsing_hour_cmd(datetime, hour)
        projection_cmd = {"carno": 1, "date": 1, "date_gps": 1}
        logs = self._get_logs(datetime=datetime, collection_type='gpslog', query_cmd=query_cmd, projection_cmd=projection_cmd)
        if logs.empty:
            return logs
        logs['date_gps'] = pd.to_datetime(logs['date_gps'])
        return logs

    def get_drivelog_hourly(self, datetime: datetime, hour: int):
        query_cmd = parsing_hour_cmd(datetime, hour)
        projection_cmd = {"carno": 1, "date": 1, "date_gps": 1}
        logs = self._get_logs(datetime=datetime, collection_type='drivelog', query_cmd=query_cmd,
                              projection_cmd=projection_cmd)
        if logs.empty:
            return logs
        logs['date_gps'] = pd.to_datetime(logs['date_gps'])
        return logs