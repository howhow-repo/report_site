# coding=utf-8
from .center_db import *
from datetime import datetime, timedelta
from decouple import config

TIME_SHIFT = config('TIME_SHIFT', default='0')


class StationCenter(CenterDB):
    def __init__(self, sqlOption: dict):
        super().__init__(sqlOption)

    def get_data_traffic(self,date: datetime):
        sql_cmd = f"""
                SELECT date, hour, gps_data_count, drivelog_data_count, bus_on_rail_count, bus_online_count FROM bus.data_traffic
                where date between '{date.strftime("%Y-%m-%d")}' and '{date.strftime("%Y-%m-%d")} 23:59:59' 
                """
        return self._get_table_data("data_traffic", sql_cmd=sql_cmd)

    def get_weekdayType(self, date: datetime):
        """
        get weekday type from database.
        if database did not mention, weekday = 0, weekend = 1
        """
        date_str = date.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT holidayCategoryType FROM bus.calendar 
                  where bus.calendar.date = '{date_str}'"""
        type = self._get_single_data(sql_cmd)
        if type is not None:
            return type
        else:
            if date.weekday() > 5:
                return 1
            else:
                return 0

    def get_rid_list_by_date(self, start_time: datetime, end_time: datetime = None) -> list:
        if end_time is None:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"SELECT rid FROM bus.schedule where starttime between '{start_time}' and '{end_time}' group by rid"
        temp = self._get_table_data("schedule", sql_cmd=sql_cmd)
        temp = temp["rid"].tolist()
        rids = [i for i in temp if i]
        return rids

    def get_schedule_by_rid(self, rid: int, start_time: datetime, end_time: datetime = None) -> pd.DataFrame:
        if start_time.hour <= int(TIME_SHIFT):
            start_time = start_time - timedelta(days=1)
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT * FROM bus.schedule 
                  where rid = {rid} and starttime between '{start_time} {TIME_SHIFT}' and '{end_time} {TIME_SHIFT}' 
                  order by starttime"""
        return self._get_table_data("schedule", sql_cmd=sql_cmd)

    def get_rids_list_by_vid(self, vid: int) -> list:
        sql_cmd = f"""SELECT id as rid FROM bus.route 
                  where vid = {vid};"""
        rids_in_df = self._get_table_data("schedule", sql_cmd=sql_cmd)
        return rids_in_df['rid'].tolist()

    def get_arrivaltime(self):
        return self._get_table_data("arrivaltime")

    def get_route_rsid(self, rid: int):
        return self._get_table_data("routestop",
                                    f"""SELECT id as rsid FROM bus.routestop where rid = {rid} 
                                    and valid = 1 order by seqno""")

    def get_route_vid(self, rid: int):
        return self._get_single_data(f"SELECT vid FROM bus.route where id = {rid};")

    def get_vid_ch_name(self, vid: int):
        return self._get_single_data(f"SELECT name FROM bus.vendor where id = {vid};")

    def get_vids_ch_name(self):
        return self._get_table_data("", f"SELECT bus.vendor.id as vid, bus.vendor.name FROM bus.vendor;")

    def get_route_ch_name(self, rid: int):
        return self._get_single_data(f"SELECT name FROM bus.route where id = {rid}")

    def get_routes_ch_name(self):
        return self._get_table_data("", f"SELECT bus.route.id as rid, bus.route.name FROM bus.route;")

    def get_route_eng_name(self, rid: int):
        return self._get_single_data(f"SELECT ename FROM bus.route where id = {rid}")

    def get_route_stops_name(self, rid: int):
        sql_cmd = f"""select name from (SELECT sid FROM bus.routestop where rid = {rid} and valid = 1 order by seqno) as t 
                  left join bus.stop on t.sid = bus.stop.id"""
        sql_cmd = sql_cmd.replace('[', '')
        sql_cmd = sql_cmd.replace(']', '')
        return self._get_table_data("routestop", sql_cmd)

    def get_first_stop_name(self, rid: int):
        sql_cmd = f"""select name from (SELECT sid FROM bus.routestop where rid = {rid} and valid = 1 and seqno = 1 
                  order by seqno) as t 
                  left join bus.stop on t.sid = bus.stop.id"""
        name = self._get_single_data(sql_cmd)
        return name

    def get_first_stop_sid(self, rid: int):
        first_sid = self._get_single_data(
            f"SELECT sid FROM bus.routestop where rid = {rid} and valid = 1 and seqno = 1")
        if first_sid is not None:
            return first_sid
        else:
            raise ValueError("can not find first stop")

    def get_schedule_logs_by_rid(self, rid: int, start_time: datetime, end_time: datetime = None):
        if end_time is None:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT 
                    bus.schedule.*,
                    bus.runlogs.carno,
                    vid,
                    bus_departure_time,
                    departure_timedelta,
                    run_stop_rate,
                    error_code 
                FROM 
                    bus.schedule 
                LEFT JOIN 
                    bus.runlogs ON bus.runlogs.schedule_id = bus.schedule.id 
                WHERE 
                    bus.schedule.rid = {rid} 
                        AND starttime BETWEEN '{start_time}' AND '{end_time}' 
                ORDER BY starttime"""
        return self._get_table_data("schedule", sql_cmd=sql_cmd)

    def get_run_stop_rate(self, start_time: datetime, end_time: datetime = None, other_filter: str = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"""SELECT 
                        * 
                    FROM 
                        (SELECT 
                            rl.rid,
                            r.name AS rid_ch_name,
                            COUNT(*) AS runs_count,
                            AVG(rl.run_stop_rate) AS avg_run_stop_rate 
                        FROM 
                            bus.runlogs AS rl 
                        LEFT JOIN bus.route AS r ON r.id = rl.rid 
                        WHERE 
                            bus_departure_time BETWEEN '{start_time}' AND '{end_time}' 
                        GROUP BY rl.rid , r.name) AS org_t """

        if other_filter is not None:
            sql_cmd += (" " + other_filter)
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table

    def get_run_logs_by_rid(self, rid: int, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT 
                        * 
                    FROM 
                        bus.runlogs 
                    WHERE 
                        rid = {rid} 
                            AND bus_departure_time BETWEEN '{start_time}' AND '{end_time}' 
                    ORDER BY bus_departure_time;"""
        table = self._get_table_data("schedule", sql_cmd=sql_cmd)
        return table

    def get_rid_schedule_run_logs(self, rid: int, start_time: datetime, end_time: datetime = None,
                                  off_duty_timedelta: int = 1200):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT 
                    bus.schedule.id,
                    bus.schedule.starttime,
                    bus.runlogs.carno,
                    bus.runlogs.cid,
                    bus.runlogs.did,
                    bus.schedule.rid,
                    bus.runlogs.bus_departure_time,
                    bus.runlogs.bus_departure_stop,
                    bus.runlogs.departure_timedelta,
                    bus.runlogs.error_code 
                FROM 
                    bus.schedule 
                        LEFT JOIN 
                    bus.runlogs ON bus.runlogs.schedule_id = bus.schedule.id 
                WHERE 
                    bus.schedule.rid = {rid} 
                        AND starttime BETWEEN '{start_time}' AND '{end_time}' 
                        AND (departure_timedelta IS NULL 
                        OR ABS(departure_timedelta) < {off_duty_timedelta}) 
                ORDER BY starttime"""
        table = self._get_table_data("schedule", sql_cmd=sql_cmd)
        table.drop_duplicates(subset='starttime', ignore_index=True, inplace=True)
        return table

    def get_run_logs_by_carno(self, carno: str, start_time: datetime, end_time: datetime = None) -> pd.DataFrame:
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"""SELECT 
                    bus.runlogs.rid,
                    bus.route.name AS rid_ch_name,
                    bus.runlogs.did,
                    bus.runlogs.vid,
                    bus.runlogs.schedule_departure_time,
                    bus.runlogs.bus_departure_time,
                    bus.runlogs.bus_departure_stop,
                    dep.name AS bus_departure_sne,
                    bus.runlogs.departure_timedelta,
                    bus.runlogs.route_stops_count,
                    bus.runlogs.run_stop_rate,
                    bus.runlogs.traveled_stops_count,
                    bus.runlogs.bus_arrival_time,
                    bus.runlogs.bus_arrival_stop,
                    arr.name AS bus_arrival_sne,
                    bus.runlogs.error_code 
                FROM 
                    bus.runlogs 
                        LEFT JOIN 
                    bus.route ON bus.runlogs.rid = bus.route.id 
                        LEFT JOIN 
                    (SELECT 
                        bus.routestop.id AS rsid, bus.routestop.sid, bus.stop.name 
                    FROM 
                        bus.routestop 
                    LEFT JOIN bus.stop ON bus.routestop.sid = bus.stop.id) AS dep ON dep.rsid = bus.runlogs.bus_departure_stop 
                        LEFT JOIN 
                    (SELECT 
                        bus.routestop.id AS rsid, bus.routestop.sid, bus.stop.name 
                    FROM 
                        bus.routestop 
                    LEFT JOIN bus.stop ON bus.routestop.sid = bus.stop.id) AS arr ON arr.rsid = bus.runlogs.bus_arrival_stop 
                WHERE 
                    bus_departure_time BETWEEN '{start_time}' AND '{end_time}' 
                        AND carno = '{carno}' 
                ORDER BY bus_departure_time"""
        return self._get_table_data("runlogs", sql_cmd=sql_cmd)

    def get_carno_list_departed_by_date(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"""SELECT carno FROM bus.runlogs 
                  where bus_departure_time between '{start_time}' and '{end_time}' group by carno;"""
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        carno_list = table['carno'].tolist()
        return carno_list

    def get_runs_count_by_date(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f""" SELECT 
                    carno,
                    COUNT(*) AS count_of_runs,
                    SUM(traveled_stops_count) AS count_of_traveled_stop 
                FROM 
                    bus.runlogs 
                WHERE 
                    bus_departure_time BETWEEN '{start_time}' AND '{end_time}' 
                GROUP BY carno
                """
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table

    def get_carno_list_by_vid(self, vid: int) -> list:
        sql_cmd = f"""SELECT no as carno FROM bus.car 
                  where vid = {vid};"""
        l = self._get_table_data("car", sql_cmd=sql_cmd)
        l = l['carno'].tolist()
        return l

    def get_runs_not_on_schedule(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT 
                    bus.runlogs.rid,
                    bus.route.name AS rid_name,
                    bus.runlogs.carno,
                    bus.runlogs.cid,
                    bus.runlogs.vid,
                    bus.runlogs.did,
                    bus.runlogs.bus_departure_time,
                    bus.runlogs.bus_departure_stop,
                    dep.name AS bus_departure_sne,
                    bus.runlogs.bus_arrival_time,
                    bus.runlogs.bus_arrival_stop,
                    arr.name AS bus_arrival_sne,
                    bus.runlogs.traveled_stops_count,
                    bus.runlogs.route_stops_count,
                    bus.runlogs.run_stop_rate,
                    bus.runlogs.weekdayType,
                    bus.runlogs.error_code 
                FROM 
                    bus.runlogs 
                        LEFT JOIN 
                    bus.route ON bus.runlogs.rid = bus.route.id 
                        LEFT JOIN 
                    (SELECT 
                        bus.routestop.id AS rsid, bus.routestop.sid, bus.stop.name 
                    FROM 
                        bus.routestop 
                    LEFT JOIN bus.stop ON bus.routestop.sid = bus.stop.id) AS dep ON bus.runlogs.bus_departure_stop = dep.rsid 
                        LEFT JOIN 
                    (SELECT 
                        bus.routestop.id AS rsid, bus.routestop.sid, bus.stop.name 
                    FROM 
                        bus.routestop 
                    LEFT JOIN bus.stop ON bus.routestop.sid = bus.stop.id) AS arr ON bus.runlogs.bus_arrival_stop = arr.rsid 
                WHERE 
                    bus_departure_time BETWEEN '{start_time}' and '{end_time}'  
                        AND schedule_id IS NULL;"""
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        table.sort_values(by='rid', ignore_index=True, inplace=True)
        return table

    def get_runs_with_error(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT 
                    bus.runlogs.rid, 
                    bus.route.name AS rid_name, 
                    bus.runlogs.carno, 
                    bus.runlogs.cid, 
                    bus.runlogs.vid, 
                    bus.runlogs.did, 
                    bus.runlogs.bus_departure_time, 
                    bus.runlogs.bus_departure_stop, 
                    dep.name AS bus_departure_sne, 
                    bus.runlogs.run_stop_rate, 
                    bus.runlogs.weekdayType, 
                    bus.runlogs.error_code 
                FROM 
                    bus.runlogs 
                        LEFT JOIN 
                    bus.route ON bus.runlogs.rid = bus.route.id 
                        LEFT JOIN 
                    (SELECT 
                        bus.routestop.id AS rsid, bus.routestop.sid, bus.stop.name 
                    FROM 
                        bus.routestop 
                    LEFT JOIN bus.stop ON bus.routestop.sid = bus.stop.id) AS dep ON bus.runlogs.bus_departure_stop = dep.rsid 
                WHERE
                    bus_departure_time BETWEEN '{start_time}' AND '{end_time}'
                        AND error_code != 0; """
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        table.sort_values(by=['rid', 'bus_departure_time'], ignore_index=True, inplace=True)
        return table

    def get_on_time_rate(self, start_time: datetime, off_duty_tol:int = 1200, early_tol: int = 60,
                         delay_tol: int = 300, end_time: datetime = None, other_filter: str = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"""SELECT  
                tt.rid,
                tt.name as rid_name,
                COUNT(*) as duty_count,
                COUNT(if((-{early_tol}<=tt.departure_timedelta) and (tt.departure_timedelta<={delay_tol}) and (tt.error_code & 32 != 32),1,null)) as on_time_departure,
                COUNT(if(tt.bus_departure_time is null,1,null)) as off_duty,
                COUNT(if (tt.error_code & 32 = 32,1,null)) as not_from_first_stop,
                COUNT(if(-{early_tol}>tt.departure_timedelta,1,null)) as early_departure,
                COUNT(if({delay_tol}<tt.departure_timedelta,1,null)) as delay_departure,
                COUNT(if((-{early_tol}<=tt.departure_timedelta) and (tt.departure_timedelta<={delay_tol}) and (tt.error_code & 32 != 32),1,null))
                /COUNT(*) as on_time_rate
                
                FROM( 
                    SELECT DISTINCT(bus.schedule.id), bus.schedule.starttime, 
                        rl.carno,rl.cid,rl.did,bus.schedule.rid,r.name,rl.schedule_id, 
                        rl.bus_departure_time,rl.bus_departure_stop,
                        rl.departure_timedelta,rl.error_code 
                    FROM bus.schedule
                        left join (SELECT rl.* FROM bus.runlogs as rl
                            inner JOIN(
                                  SELECT schedule_id, 
                                  MIN(abs(departure_timedelta)) as min_departure_timedelta,
                                  SUBSTRING_INDEX(group_concat(carno),',',1) as carno
                                  FROM  bus.runlogs
                                  where bus_departure_time between  '{start_time}' 
                                        and '{end_time}' 
                                        and (error_code & 32 != 32)
                                  GROUP BY  schedule_id) as tbl
                             ON rl.schedule_id = tbl.schedule_id
                             where bus_departure_time between  '{start_time}' and '{end_time}'
                             and tbl.min_departure_timedelta = abs(rl.departure_timedelta)
                             and tbl.carno = rl.carno
                        ) as rl ON rl.schedule_id = bus.schedule.id
                        left join bus.route as r ON r.id = bus.schedule.rid
                    where starttime between  '{start_time}' and '{end_time}'
                    and (departure_timedelta is null or abs(departure_timedelta) < {off_duty_tol}) 
                    order by rid , starttime
                    )as tt """

        if other_filter is not None:
            sql_cmd += (" "+other_filter)
        sql_cmd += "group by rid,name"
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table

    def delete_runlogs_by_date(self, start_date: datetime, end_date: datetime = None):
        if end_date is None:
            end_date = start_date
        end_date = end_date + timedelta(days=1)
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        sql_cmd = f"""
            DELETE FROM bus.runlogs 
            WHERE bus_departure_time between '{start_date} {TIME_SHIFT}' and '{end_date} {TIME_SHIFT}'
        """
        return self._delete_data(sql_cmd)

    def delete_stoptostop_by_date(self, start_date: datetime, end_date: datetime = None):
        if end_date is None or end_date == start_date:
            end_date = start_date
        end_date = end_date + timedelta(days=1)
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        sql_cmd = f"""
            DELETE FROM bus.stoptostop 
            WHERE departure_time between '{start_date} {TIME_SHIFT}' and '{end_date} {TIME_SHIFT}'
            or arrival_time between '{start_date} {TIME_SHIFT}' and '{end_date} {TIME_SHIFT}'
        """
        return self._delete_data(sql_cmd)

