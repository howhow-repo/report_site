import json
import os
from background_task import background
from datetime import datetime, timedelta

from dotenv import load_dotenv

from .reportsLib import DailyInfoStaker

from .models import add_exception_bus, add_parsing_result


def test():
    print(f'{datetime.now()} loopppp')


def stacking_runs_and_stoptostop():
    load_dotenv()
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))
    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    process_date = datetime.today() - timedelta(days=1)
    result = daily_stacker.start(process_date)
    add_parsing_result(date=process_date, bus_count=result['bus_count'], runs_count=result['runs_count'],
                       exception_bus_count=result['exception_bus_count'], error_code=result['error_code'],
                       time_spent=result['time_spent'])
    add_exception_bus(daily_stacker.exception_bus, datetime.today() - timedelta(days=1))

    return result



def trigger_stacking():
    result = stacking_runs_and_stoptostop()
    return result
