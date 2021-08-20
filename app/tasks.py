import json
import os
import requests
from urllib import parse
from datetime import datetime, timedelta
from decouple import config
from .reportsLib import DailyInfoStaker
from .models import add_exception_bus, add_parsing_result

PROJECT_TITLE = config('PROJECT_TITLE', default='unnamed')


def sql_conn_heartbeat():
    from core.urls import scheduler
    print(f"[{datetime.now()}] sql_conn_heartbeat: {scheduler.get_job('sql_conn_heartbeat')}")
    return 0


def stacking_runs_and_stoptostop(start_date: datetime = None, end_date: datetime = None) -> list:
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

    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    for day in days:
        result = daily_stacker.start(start_date=day, redo=True)
        results.append(result)
        add_parsing_result(date=day, bus_count=result['bus_count'], runs_count=result['runs_count'],
                           stoptostop_count=result['stoptostop_count'],
                           exception_bus_count=result['exception_bus_count'],
                           error_code=result['error_code'], time_spent=result['time_spent'])
        add_exception_bus(result['exception_buses'], day)

        try:
            send_line_notify(f"[{PROJECT_TITLE}][runs task]" + str(result))
        except Exception as err:
            pass

    return results


def send_line_notify(text):
    TOKEN = os.getenv("LINE_TOKEN")
    url = "https://notify-api.line.me/api/notify"
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + TOKEN
    }
    payload = parse.urlencode({'message': str(text)})
    response = requests.post(url, data=payload, headers=headers)
    return response
