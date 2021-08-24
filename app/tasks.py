import json
import os
import requests
from urllib import parse
from datetime import datetime, timedelta
from decouple import config
from .reportsLib import DailyInfoStaker
from .models import add_exception_bus, add_parsing_result, DailyDriveLogParsingStatus, ExceptionParsingBus
from notify.models import LineNotifyControl

PROJECT_TITLE = config('PROJECT_TITLE', default='unnamed')


def sql_conn_keepalive():
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

    return results


def task_report_notification():
    latest_data = DailyDriveLogParsingStatus.objects.order_by('-date')[0]
    latest_date = latest_data.date
    if latest_date != datetime.today().date() - timedelta(days=1):
        send_line_notify(f"[{PROJECT_TITLE}][runs task]: \n !!WARNRING!! \n"
                         f"The stacking_runs_and_stoptostop did not run yesterday!")
        send_line_notify(f"{type(latest_data.date)}")
    else:
        excep_buses = ExceptionParsingBus.objects.filter(date=datetime.today().date() - timedelta(days=1)).order_by(
            '-date')

        send_line_notify(f"[{PROJECT_TITLE}][runs task]: \n"
                         f"統計日期: {latest_data.date} \n"
                         f"遍歷公車數量: {latest_data.buses_count} \n"
                         f"結果趟次數量: {latest_data.runs_count} \n"
                         f"站到站數量: {latest_data.stoptostop_count} \n"
                         f"計算花費時間(s): {latest_data.time_spent} \n"
                         f"例外公車: {[b.carno for b in excep_buses]} \n"
                         f"error_code: {latest_data.error_code}")


def send_line_notify(text):
    people_to_sent = LineNotifyControl.objects.filter(activate=True)
    for p in people_to_sent:
        try:
            TOKEN = p.token
            url = "https://notify-api.line.me/api/notify"
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer ' + TOKEN
            }
            payload = parse.urlencode({'message': str(text)})
            requests.post(url, data=payload, headers=headers)
        except Exception as e:
            print(f'sent notify to {p.name}:{p.token} fail.')
            print(e)
            continue

    # if define in .env, also send
    t = config("LINE_TOKEN", default=None)
    if t is not None:
        try:
            TOKEN = t
            url = "https://notify-api.line.me/api/notify"
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer ' + TOKEN
            }
            payload = parse.urlencode({'message': str(text)})
            requests.post(url, data=payload, headers=headers)
        except Exception as e:
            print(f'sent notify to {t} in .env fail.')
            print(e)

    print("---send line notify done")
