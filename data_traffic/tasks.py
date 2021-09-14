import json, os
from datetime import datetime, timedelta

from app.reportsLib import DailyDataTrafficStaker
from .models import add_data_traffic_parsing_result


def stacking_data_traffic(start_date: datetime = None, end_date: datetime = None):
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))
    results = []
    if start_date is None:
        assert end_date is None
        days = [datetime.today() - timedelta(days=1)]
    else:
        days = [start_date]
        if end_date is not None:
            assert end_date >= start_date
            d = start_date
            while d < end_date:
                d += timedelta(days=1)
                days.append(d)
    daily_traffic_stacker = DailyDataTrafficStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    for day in days:
        result = daily_traffic_stacker.start(start_date=day, redo=True)
        results.append(result)
        add_data_traffic_parsing_result(date=day, time_spent=result['time_spent'], status=result['status'])

    return results
