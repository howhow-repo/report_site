import inspect
import json
from datetime import datetime
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import parsing_post_report
from rest_framework.views import APIView

from app.reportsLib import ReportCenter


class ListReports(APIView):
    def get(self, request):
        rc = ReportCenter()
        index_table = {}
        for i, rn in enumerate(rc.report_list):
            r = rc.create_empty_report(rn)
            index_table[i] = ({"report_name": rn, "title": r.title, "simple_description": r.simple_description,
                                "args": list(inspect.signature(r.generate_report).parameters)})
        return JsonResponse(index_table)

class ReportAPIView(APIView):

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'start_time': openapi.Schema(type=openapi.TYPE_STRING, description='%Y-%m-%d'),
            'end_time': openapi.Schema(type=openapi.TYPE_STRING, description='%Y-%m-%d'),
            'carno': openapi.Schema(type=openapi.TYPE_STRING, description='車牌號碼'),
            'vid': openapi.Schema(type=openapi.TYPE_INTEGER, description='營運商id'),
            'rid': openapi.Schema(type=openapi.TYPE_INTEGER, description='路線id'),
            'type': openapi.Schema(type=openapi.TYPE_STRING, description='json/csv/html/pdf, default=json'),

        }
    ))
    def post(self, request, report_name):
        body = json.loads(request.body.decode('utf-8'))
        para_received = body
        para_received = format_paras(para_received)
        return parsing_post_report(request=request, rtype=report_name, para_received=para_received)

def format_paras(para_received: dict):
    for para in para_received:
        try:
            if str.isnumeric(para_received[para]):
                para_received[para] = int(para_received[para])
        except Exception:
            continue

    if "start_time" in para_received:
        para_received["start_time"] = datetime.strptime(para_received["start_time"], '%Y-%m-%d')
    if "end_time" in para_received:
        para_received["end_time"] = datetime.strptime(para_received["end_time"], '%Y-%m-%d')

    if "csrfmiddlewaretoken" in para_received:
        del para_received['csrfmiddlewaretoken']
    return para_received