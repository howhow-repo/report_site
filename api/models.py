from django.db import models
import datetime
import inspect
import json
import os

import pdfkit
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.template import loader
from dotenv import load_dotenv

from app.reportsLib import ReportCenter

load_dotenv()
sql_options = json.loads(os.getenv("EBUS_SQLDB"))
mongo_options = json.loads(os.getenv("EBUS_MONGODB"))

# Create your models here.
def parsing_post_report(request, rtype, para_received):
    rc = ReportCenter(centerDB_conn_options=sql_options, drivelogDB_conn_options=mongo_options)
    report = rc.create_empty_report(rtype)
    report.generate_report(**para_received)
    if "type" in para_received.keys():
        if para_received['type'] == 'json':
            r = report.report.to_dict("records")
            return JsonResponse(r,safe=False)

        elif para_received['type'] == 'csv':
            return HttpResponse(report.report.to_csv(), content_type="application/csv")

        elif para_received['type'] == 'html':
            return HttpResponse(report.parsing_df_for_user().to_html(), content_type="application/html")

        elif para_received['type'] == 'pdf':
            context = {
                'rtype': rtype,
                'title': report.title,
                'sub_title': report.sub_title,
                'sub_title2': report.sub_title2,
                'start_time': report.start_time,
                'end_time': report.end_time,
                'report': report.parsing_df_for_user().to_html(),
            }
            load_template = 'app/report_simple.html'
            html_template = loader.get_template(load_template)
            html_string = html_template.render(context, request)
            pdf = pdfkit.from_string(html_string, False)
            response = HttpResponse(pdf, content_type='application/pdf')
            response[
                'Content-Disposition'] = f'filename="{rtype + "_" + report.start_time.strftime("%Y_%m_%d")}.pdf"'
            return response
    else:
        r = report.report.to_dict("records")
        return JsonResponse(r, safe=False)
