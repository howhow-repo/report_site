from datetime import datetime, timedelta
from dotenv import load_dotenv
from .reportsLib import DailyInfoStaker
import os, json


def test():
    print(f'{datetime.now()} loopppp')


def runsAndStopStacking():
    load_dotenv()
    sql_options = json.loads(os.getenv("EBUS_SQLDB"))
    mongo_options = json.loads(os.getenv("EBUS_MONGODB"))
    daily_stacker = DailyInfoStaker(MongoDBOptions=mongo_options, sqlOption=sql_options)
    daily_stacker.start(datetime.today() - timedelta(days=1))
