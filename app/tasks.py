import json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from .reportsLib import DailyInfoStaker


def test():
    print(f'{datetime.now()} loopppp')


def stacking_runs_and_stoptostop():
    load_dotenv()
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))
    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    daily_stacker.start(datetime.today() - timedelta(days=1))
