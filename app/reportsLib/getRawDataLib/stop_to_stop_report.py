from .station_center import StationCenter
from datetime import datetime, timedelta
import pandas as pd


def to_sqllist(l: list) -> str:
    l = str(l)
    l = l.replace('[', '(')
    l = l.replace(']', ')')
    return l


class StopToStopResult(StationCenter):
    def get_default_stop_to_stop_by_rid(self, rid: int,
                                        date_begin: datetime = (datetime.today() - timedelta(days=30)).strftime(
                                            "%Y-%m-%d"),
                                        date_end: datetime = (datetime.today()).strftime("%Y-%m-%d"),

                                        hour_begin: int = 0,
                                        hour_end: int = 24,
                                        weekdayType=None,
                                        **kwargs) -> pd.DataFrame:
        if weekdayType is None:
            weekdayType = [0, 1, 2, 3, 4, 5, 6]
        assert (0 <= hour_begin <= 24) and (0 <= hour_end <= 24) and (hour_begin <= hour_end)
        hour_begin = str(hour_begin).zfill(2)
        hour_end = str(hour_end).zfill(2)
        weekdayType = to_sqllist(weekdayType)
        sql_cmd = f"""SELECT 
            tt.rsid,
            rsnow.sid,
            s.name,
            tt.previous_rsid,
            rspre.sid AS previous_sid,
            s_pre.name AS previous_name,
            tt.max_arrival_time_spent,
            tt.min_arrival_time_spent,
            tt.avg_arrival_time_spent,
            tt.std_arrival_time_spent,
            tt.var_arrival_time_spent,
            tt.max_stay_time,
            tt.min_stay_time,
            tt.avg_stay_time,
            tt.std_stay_time,
            tt.var_stay_time,
            tt.sample_count
        FROM
            (SELECT 
                rsid,
                previous_rsid,
                MAX(arrival_time_spent) AS max_arrival_time_spent,
                MIN(arrival_time_spent) AS min_arrival_time_spent,
                AVG(arrival_time_spent) AS avg_arrival_time_spent,
                STDDEV(arrival_time_spent) AS std_arrival_time_spent,
                VAR_POP(arrival_time_spent) AS var_arrival_time_spent,
                MAX(stay_time) AS max_stay_time,
                MIN(stay_time) AS min_stay_time,
                AVG(stay_time) AS avg_stay_time,
                STDDEV(stay_time) AS std_stay_time,
                VAR_POP(stay_time) AS var_stay_time,
                COUNT(*) AS sample_count
            FROM
                bus.stoptostop
            WHERE
                ((arrival_time BETWEEN '{date_begin}' AND '{date_end}' AND TIME(arrival_time) BETWEEN '{hour_begin}:00:00' AND '{hour_end}:00:00')
                    OR (departure_time BETWEEN '{date_begin}' AND '{date_end}' AND TIME(departure_time) BETWEEN '{hour_begin}:00:00' AND '{hour_end}:00:00'))
                    AND error_code = 0
                    AND isFirst != 1
                    AND weekdayType in {weekdayType}
                    AND rid = {rid}
            GROUP BY rsid , previous_rsid) AS tt
                LEFT JOIN
            bus.routestop AS rsnow ON rsnow.id = tt.rsid
                LEFT JOIN
            bus.routestop AS rspre ON rspre.id = tt.previous_rsid
                LEFT JOIN
            bus.stop AS s ON s.id = rsnow.sid
                LEFT JOIN
            bus.stop AS s_pre ON s_pre.id = rspre.sid"""
        data = self._get_table_data("schedule", sql_cmd=sql_cmd)
        sql_cmd = f"""
                    SELECT 
                rs.id AS rsid, sid, s.name
            FROM
                bus.routestop AS rs
                    LEFT JOIN
                bus.stop AS s ON s.id = rs.sid
            WHERE
                rid = {rid} AND valid = 1
            ORDER BY seqno
        """
        rsids = (self._get_table_data("schedule", sql_cmd=sql_cmd).iloc[1:]).copy()

        return pd.merge(rsids, data, on=['rsid', 'sid', 'name'], how='outer')
