import json
import os
import requests
from urllib import parse

from datetime import datetime, timedelta

from dotenv import load_dotenv

from .reportsLib import DailyInfoStaker

from .models import add_exception_bus, add_parsing_result

load_dotenv()


def sql_conn_heartbeat():
    from core.urls import scheduler
    print(f"sql_conn_heartbeat: {scheduler.get_jobs()}")
    return 0


def stacking_runs_and_stoptostop(start_date: datetime = None, end_date: datetime = None):
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

    if start_date is None:
        assert end_date is None
        process_date = datetime.today() - timedelta(days=1)
    else:
        process_date = start_date
        if end_date is not None:
            assert end_date >= start_date

    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    result = daily_stacker.start(start_date=process_date, end_date=end_date, redo=True)
    add_parsing_result(date=process_date, bus_count=result['bus_count'], runs_count=result['runs_count'],
                       stoptostop_count=result['stoptostop_count'], exception_bus_count=result['exception_bus_count'],
                       error_code=result['error_code'], time_spent=result['time_spent'])
    add_exception_bus(result['exception_buses'], datetime.today() - timedelta(days=1))

    try:
        send_line_notify("[PingDong][runs task]" + str(result))
    except Exception as err:
        pass

    return result


def trigger_stacking(start_date: datetime = None, end_date: datetime = None):
    result = stacking_runs_and_stoptostop(start_date=start_date, end_date=end_date)
    return result


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
