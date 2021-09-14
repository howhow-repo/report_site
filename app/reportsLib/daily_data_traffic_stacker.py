from datetime import datetime, timedelta
from .getRawDataLib import DataTrafficCounter

import logging

logger = logging.getLogger(__name__)


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


class DailyDataTrafficStaker:
    '''
        use to calculate everyday GPS log data count for each hour.
        To show how many data can be handle per hour.
    '''

    def __init__(self, MongoDBOptions: dict, sqlOption: dict):
        self.data_traffic = DataTrafficCounter(MongoDBPath=MongoDBOptions, sqlOption=sqlOption)

    def start(self, start_date: datetime = None, end_date: datetime = None,
              redo: bool = True):
        stime = datetime.now()

        if start_date is None:
            start_date = datetime.now() - timedelta(days=1)

        if end_date is None:
            end_date = start_date
        else:
            assert end_date >= start_date

        days = days_in_list(start_date, end_date)
        exception_days = []
        self.data_traffic.connect()
        # calculate
        status = True
        for day in days:
            ptime = datetime.now()
            print(f'  Parsing data traffic of date {day.strftime("%Y-%m-%d")} ...')
            try:
                self.data_traffic.get_daily_traffic(datetime=day)
                self.data_traffic.save_data_to_sql(redo=redo)
            except Exception as e:
                exception_days.append(day)
                status = False
            print(f"  done, time spent {int((datetime.now()-ptime).seconds)} (s)\n")

        self.data_traffic.disconnect()
        time_spent = int((datetime.now() - stime).seconds)
        print(f'----Time spent: {time_spent} (s)----')
        return {
            'date': [d.strftime("%Y-%m-%d") for d in days],
            'exception_days': [d.strftime("%Y-%m-%d") for d in exception_days],
            'time_spent': time_spent,
            'status': status
        }
