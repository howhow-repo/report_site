import inspect
import json
from datetime import datetime
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import parsing_post_report
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from app.reportsLib import ReportCenter


class ListReports(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rc = ReportCenter()
        index_table = {}
        for i, rn in enumerate(rc.report_list):
            r = rc.create_empty_report(rn)
            index_table[i] = ({"report_name": rn, "title": r.title, "simple_description": r.simple_description,
                                "args": list(inspect.signature(r.generate_report).parameters)})
        return JsonResponse(index_table)


class ListJobs(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.urls import scheduler
        j_json = {}
        for i, j in enumerate(scheduler.get_jobs()):
            j_json[str(i)] = {"name": j.name, "next_run_time": str(j.next_run_time), "trigger": str(j.trigger)}
        return JsonResponse(j_json)


class ReportAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'start_time': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d'),
            'end_time': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d, default=today'),
            'carno': openapi.Schema(type=openapi.TYPE_STRING, description='車牌號碼'),
            'vid': openapi.Schema(type=openapi.TYPE_INTEGER, description='營運商id'),
            'rid': openapi.Schema(type=openapi.TYPE_INTEGER, description='路線id'),
            'type': openapi.Schema(type=openapi.TYPE_STRING, description='json/csv/html/pdf, default=json'),
            'off_duty_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間超出？秒即脫班, default=1200'),
            'early_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間提早表訂時間逾?秒鐘，視為早發, default=60'),
            'delay_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間超過表訂時間逾?秒鐘，視為遲發, default=300'),

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
            para_received[para] = int(para_received[para])
        except Exception:
            continue

    if "start_time" in para_received:
        para_received["start_time"] = datetime.strptime(para_received["start_time"], '%Y-%m-%d')
    if "end_time" in para_received:
        para_received["end_time"] = datetime.strptime(para_received["end_time"], '%Y-%m-%d')

    return para_received