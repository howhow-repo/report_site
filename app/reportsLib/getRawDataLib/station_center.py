import pandas as pd

from .center_db import *
from datetime import datetime, timedelta


class StationCenter(CenterDB):
    def __init__(self, sqlOption: dict):
        super().__init__(sqlOption)

    def get_weekdayType(self, date: datetime):
        date = date.strftime("%Y-%m-%d")
        sql_cmd = f"SELECT holidayCategoryType FROM bus.calendar " \
                  f"where bus.calendar.date = '{date}'"
        type = self._get_single_data(sql_cmd)
        if type is None:
            return 0
        else:
            return type

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
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"SELECT * FROM bus.schedule where rid = {rid} and starttime between '{start_time}' and '{end_time}' " \
                  f"order by starttime";
        return self._get_table_data("schedule", sql_cmd=sql_cmd)

    def get_rids_list_by_vid(self, vid: int) -> list:
        sql_cmd = f"SELECT id as rid FROM bus.route " \
                  f"where vid = {vid};"
        rids_in_df = self._get_table_data("schedule", sql_cmd=sql_cmd)
        return rids_in_df['rid'].tolist()

    def get_arrivaltime(self):
        return self._get_table_data("arrivaltime")

    def get_route_rsid(self, rid: int):
        return self._get_table_data("routestop",
                                    f"SELECT id as rsid FROM bus.routestop where rid = {rid} "
                                    f"and valid = 1 order by seqno")

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
        sql_cmd = f"select name from (SELECT sid FROM bus.routestop where rid = {rid} and valid = 1 order by seqno) as t " \
                  f"left join bus.stop on t.sid = bus.stop.id"
        sql_cmd = sql_cmd.replace('[', '')
        sql_cmd = sql_cmd.replace(']', '')
        return self._get_table_data("routestop", sql_cmd)

    def get_first_stop_name(self, rid: int):
        sql_cmd = f"select name from (SELECT sid FROM bus.routestop where rid = {rid} and valid = 1 and seqno = 1 " \
                  f"order by seqno) as t " \
                  f"left join bus.stop on t.sid = bus.stop.id"
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
        sql_cmd = "SELECT bus.schedule.*, bus.runlogs.carno,vid,bus_departure_time, departure_timedelta, " \
                  "run_stop_rate, error_code " \
                  "FROM bus.schedule " \
                  "left join bus.runlogs ON bus.runlogs.schedule_id = bus.schedule.id " \
                  f"where bus.schedule.rid = {rid} " \
                  f"and starttime between '{start_time}' and '{end_time}' " \
                  "order by starttime"
        return self._get_table_data("schedule", sql_cmd=sql_cmd)

    def get_run_stop_rate(self, start_time: datetime, end_time: datetime = None, other_filter: str = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"""SELECT * FROM (SELECT rl.rid, r.name as rid_ch_name, count(*) as runs_count, avg(rl.run_stop_rate) as avg_run_stop_rate  FROM bus.runlogs as rl
            left join bus.route as r on r.id = rl.rid
            where bus_departure_time between  '{start_time}' and '{end_time}'
            group by rl.rid, r.name) as org_t """

        if other_filter is not None:
            sql_cmd += other_filter
        print(sql_cmd)
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table

    def get_rid_schedule_run_logs(self, rid: int, start_time: datetime, end_time: datetime = None,
                                  off_duty_timedelta: int = 1200):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"SELECT bus.schedule.id, bus.schedule.starttime, " \
                  f"bus.runlogs.carno,bus.runlogs.cid,bus.runlogs.did,bus.schedule.rid," \
                  f"bus.runlogs.bus_departure_time,bus.runlogs.bus_departure_stop," \
                  f"bus.runlogs.departure_timedelta,bus.runlogs.error_code " \
                  f"FROM bus.schedule " \
                  f"left join bus.runlogs ON bus.runlogs.schedule_id = bus.schedule.id " \
                  f"where bus.schedule.rid = {rid} " \
                  f"and starttime between '{start_time}' and '{end_time}' " \
                  f"and (departure_timedelta is null or abs(departure_timedelta) < {off_duty_timedelta}) " \
                  f"order by starttime"
        table = self._get_table_data("schedule", sql_cmd=sql_cmd)
        table.drop_duplicates(subset='starttime', ignore_index=True, inplace=True)
        return table

    def get_run_logs_by_carno(self, carno: str, start_time: datetime, end_time: datetime = None) -> pd.DataFrame:
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"SELECT " \
                  f"bus.runlogs.rid, " \
                  f"bus.route.name as rid_ch_name, " \
                  f"bus.runlogs.did, " \
                  f"bus.runlogs.vid, " \
                  f"bus.runlogs.schedule_departure_time, " \
                  f"bus.runlogs.bus_departure_time, " \
                  f"bus.runlogs.bus_departure_stop, " \
                  f"dep.name as bus_departure_sne, " \
                  f"bus.runlogs.departure_timedelta," \
                  f"bus.runlogs.route_stops_count, " \
                  f"bus.runlogs.run_stop_rate, " \
                  f"bus.runlogs.traveled_stops_count, " \
                  f"bus.runlogs.bus_arrival_time, " \
                  f"bus.runlogs.bus_arrival_stop, " \
                  f"arr.name as bus_arrival_sne, " \
                  f"bus.runlogs.error_code " \
                  f"FROM bus.runlogs " \
                  f"left join bus.route on bus.runlogs.rid = bus.route.id " \
                  f"left join (SELECT bus.routestop.id as rsid,bus.routestop.sid,bus.stop.name FROM bus.routestop " \
                  f"left join bus.stop on bus.routestop.sid = bus.stop.id) as dep " \
                  f"on dep.rsid = bus.runlogs.bus_departure_stop " \
                  f"left join (SELECT bus.routestop.id as rsid,bus.routestop.sid,bus.stop.name FROM bus.routestop " \
                  f"left join bus.stop on bus.routestop.sid = bus.stop.id) as arr " \
                  f"on arr.rsid = bus.runlogs.bus_arrival_stop " \
                  f"where bus_departure_time between '{start_time}' and '{end_time}' " \
                  f"and carno = '{carno}' " \
                  f"order by bus_departure_time"
        return self._get_table_data("runlogs", sql_cmd=sql_cmd)

    def get_carno_list_departed_by_date(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")

        sql_cmd = f"SELECT carno FROM bus.runlogs " \
                  f"where bus_departure_time between '{start_time}' and '{end_time}' group by carno;"
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        carno_list = table['carno'].tolist()
        return carno_list

    def get_runs_count_by_date(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f""" SELECT carno, count(*) as count_of_runs ,sum(traveled_stops_count) as count_of_traveled_stop 
                FROM bus.runlogs
                where bus_departure_time between  '{start_time}' and '{end_time}'
                group by carno
                """
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table

    def get_carno_list_by_vid(self, vid: int) -> list:
        sql_cmd = f"SELECT no as carno FROM bus.car " \
                  f"where vid = {vid};"
        l = self._get_table_data("car", sql_cmd=sql_cmd)
        l = l['carno'].tolist()
        return l

    def get_runs_not_on_schedule(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"SELECT " \
                  f"bus.runlogs.rid, " \
                  f"bus.route.name as rid_name, " \
                  f"bus.runlogs.carno, " \
                  f"bus.runlogs.cid, " \
                  f"bus.runlogs.vid, " \
                  f"bus.runlogs.did, " \
                  f"bus.runlogs.bus_departure_time, " \
                  f"bus.runlogs.bus_departure_stop, " \
                  f"dep.name as bus_departure_sne, " \
                  f"bus.runlogs.bus_arrival_time, " \
                  f"bus.runlogs.bus_arrival_stop, " \
                  f"arr.name as bus_arrival_sne, " \
                  f"bus.runlogs.traveled_stops_count, " \
                  f"bus.runlogs.route_stops_count, " \
                  f"bus.runlogs.run_stop_rate, " \
                  f"bus.runlogs.weekdayType, " \
                  f"bus.runlogs.error_code " \
                  f"FROM bus.runlogs " \
                  f"left join bus.route " \
                  f"on bus.runlogs.rid = bus.route.id " \
                  f"left join  " \
                  f"(SELECT bus.routestop.id as rsid, bus.routestop.sid,bus.stop.name  " \
                  f"FROM bus.routestop left join bus.stop on bus.routestop.sid = bus.stop.id) as dep " \
                  f"on bus.runlogs.bus_departure_stop = dep.rsid " \
                  f"left join " \
                  f"(SELECT bus.routestop.id as rsid, bus.routestop.sid,bus.stop.name " \
                  f"FROM bus.routestop left join bus.stop on bus.routestop.sid = bus.stop.id)as arr " \
                  f"on bus.runlogs.bus_arrival_stop = arr.rsid " \
                  f"where bus_departure_time between '{start_time}' and '{end_time}' " \
                  f"and schedule_id is Null;"
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        table.sort_values(by='rid', ignore_index=True, inplace=True)
        return table

    def get_runs_with_error(self, start_time: datetime, end_time: datetime = None):
        if end_time is None or end_time == start_time:
            end_time = start_time
        end_time = end_time + timedelta(days=1)
        start_time = start_time.strftime("%Y-%m-%d")
        end_time = end_time.strftime("%Y-%m-%d")
        sql_cmd = f"SELECT " \
                  f"bus.runlogs.rid, " \
                  f"bus.route.name as rid_name, " \
                  f"bus.runlogs.carno, " \
                  f"bus.runlogs.cid, " \
                  f"bus.runlogs.vid, " \
                  f"bus.runlogs.did, " \
                  f"bus.runlogs.bus_departure_time, " \
                  f"bus.runlogs.bus_departure_stop, " \
                  f"dep.name as bus_departure_sne, " \
                  f"bus.runlogs.run_stop_rate," \
                  f"bus.runlogs.weekdayType, " \
                  f"bus.runlogs.error_code " \
                  f"FROM bus.runlogs " \
                  f"left join bus.route " \
                  f"on bus.runlogs.rid = bus.route.id " \
                  f"left join " \
                  f"(SELECT bus.routestop.id as rsid, bus.routestop.sid,bus.stop.name " \
                  f"FROM bus.routestop left join bus.stop on bus.routestop.sid = bus.stop.id)as dep " \
                  f"on bus.runlogs.bus_departure_stop = dep.rsid " \
                  f"where bus_departure_time between '{start_time}' and '{end_time}' " \
                  f"and error_code != 0; "
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
                count(if(-{early_tol}>tt.departure_timedelta,1,null)) as early_departure,
                count(if({delay_tol}<tt.departure_timedelta,1,null)) as delay_departure,
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
            sql_cmd += other_filter
        sql_cmd += "group by rid,name"
        table = self._get_table_data("runlogs", sql_cmd=sql_cmd)
        return table


