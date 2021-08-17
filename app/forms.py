import datetime
import json, os

from django import forms
import inspect
from dotenv import load_dotenv

from .reportsLib import ReportCenter, StationCenter

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))


class ReportPrehandle(forms.Field):
    def __init__(self, rtype):
        super().__init__()
        pass
        rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
        report = rc.create_empty_report(rtype)
        rtype_paras = list(inspect.signature(report.generate_report).parameters)
        if "start_time" in rtype_paras:
            start_time = forms.DateField()
            start_time.initial = datetime.datetime.today()
        if "end_time" in rtype_paras:
            end_time = forms.DateField()
            end_time.initial = datetime.datetime.today()
        if "rid" in rtype_paras:
            pass