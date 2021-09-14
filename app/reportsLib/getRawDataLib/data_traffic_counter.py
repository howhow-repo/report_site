import pandas as pd
from datetime import datetime, timedelta
from .gpslog_db import GpsLogDB
from .station_center import StationCenter
import logging

logger = logging.getLogger(__name__)


class DataTrafficCounter(GpsLogDB):
    def __init__(self, MongoDBPath: dict, sqlOption: dict):
        super().__init__(MongoDBPath)
        self.station_center = StationCenter(sqlOption=sqlOption)
        self.daily_result = pd.DataFrame({})
        self.date = None
        self.bus_online = []
        self.bus_on_rail = []


    def connect(self):
        super(DataTrafficCounter, self).connect()
        self.station_center.connect()

    def disconnect(self):
        super(DataTrafficCounter, self).disconnect()
        self.station_center.disconnect()

    def get_hour_traffic(self, datetime: datetime, hour: int):
        df_gpslog = self.get_gpslog_hourly(datetime, hour)
        df_drivelog = self.get_drivelog_hourly(datetime, hour)
        if df_gpslog.empty:
            df_gpslog['carno']={}
        sql_cmd = f"""
                SELECT 
                    carno 
                FROM 
                    bus.runlogs 
                WHERE 
                    bus_arrival_time BETWEEN '{datetime.strftime("%Y-%m-%d")} {hour:02d}:00:00' AND '{datetime.strftime("%Y-%m-%d")} {hour+1:02d}:00:00' 
                        OR bus_departure_time BETWEEN '{datetime.strftime("%Y-%m-%d")} {hour:02d}:00:00' AND '{datetime.strftime("%Y-%m-%d")} {hour+1:02d}:00:00' 
                        OR (bus_departure_time < '{datetime.strftime("%Y-%m-%d")} {hour:02d}:00:00' 
                        AND bus_arrival_time > '{datetime.strftime("%Y-%m-%d")} {hour+1:02d}:00:00') 
                GROUP BY carno
        """
        bus_on_rail = self.station_center._get_table_data("runlogs", sql_cmd=sql_cmd)
        self.bus_on_rail = set(bus_on_rail["carno"].tolist())
        self.bus_online = set(df_gpslog['carno'].tolist())

        return {
            'date':datetime.replace(hour=hour),
            'hour':hour,
            'gps_data_count':len(df_gpslog),
            'drivelog_data_count':len(df_drivelog),
            'bus_online_count':len(self.bus_online),
            'bus_on_rail_count':len(self.bus_on_rail),
        }

    def get_daily_traffic(self, datetime: datetime):
        self.date = datetime
        self.daily_result = pd.DataFrame({})
        for h in range(24):
            print(f'    Analysing data traffic at {datetime.strftime("%Y-%m-%d")} {h:02d}:00~{h+1:02d}:00 ...')
            hour_data = (pd.DataFrame([self.get_hour_traffic(datetime=datetime,hour=h)]))
            self.daily_result = self.daily_result.append(hour_data,ignore_index=True)
        return self.daily_result

    def save_data_to_sql(self, redo: bool = True):
        d = self.date.strftime("%Y-%m-%d")
        if redo is True:
            sql_cmd = f"""
                        DELETE FROM bus.data_traffic 
                        WHERE date between '{d} 00:00:00'  and '{d} 23:59:59'
                    """
            self.station_center._delete_data(sql_cmd)
        self.station_center.insert_data(table_name='data_traffic', data=self.daily_result)