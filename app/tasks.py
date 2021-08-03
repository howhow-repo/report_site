import json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from .reportsLib import DailyInfoStaker

from .models import add_err_bus, add_parsing_status


def test():
    print(f'{datetime.now()} loopppp')


def stacking_runs_and_stoptostop():
    load_dotenv()
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))
    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    daily_stacker.start(datetime.today() - timedelta(days=1))
    add_parsing_status(datetime.today() - timedelta(days=1), bus_count=len(daily_stacker.drove_bus),
                       error_bus_count=len(daily_stacker.err_bus), error_code=daily_stacker.error_code)
    add_err_bus(daily_stacker.err_bus,datetime.today() - timedelta(days=1))

