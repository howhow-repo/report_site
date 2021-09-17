# -*- coding: UTF-8 -*-
import inspect
import json
import logging
import os
from datetime import datetime, timedelta
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from app.tasks import stacking_runs_and_stoptostop
from data_traffic.tasks import stacking_data_traffic
from .models import parsing_post_report
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication

from app.reportsLib import ReportCenter, StopToStopResult
from app.tasks import task_report_notification


logger = logging.getLogger(__name__)


class ListReports(APIView):
    """
        使用此api獲得支援的報表類型與敘述。
        亦可在此查詢報表產生所需的參數。
    """

    @swagger_auto_schema(
        operation_summary='Use to check supported reports and parameters.'
    )
    def get(self, request):
        rc = ReportCenter()
        index_table = {}
        for i, rn in enumerate(rc.report_list):
            r = rc.create_empty_report(rn)
            index_table[i] = ({"report_name": rn, "title": r.title, "simple_description": r.simple_description,
                                "args": list(inspect.signature(r.generate_report).parameters)})
        return JsonResponse(index_table)


class ListJobs(APIView):
    """
        列出背景執行程式及其狀態。
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to check background tasks status.'
    )
    def get(self, request):
        from core.urls import scheduler
        j_json = {}
        for i, j in enumerate(scheduler.get_jobs()):
            j_json[str(i)] = {"name": j.name, "id":j.id, "next_run_time": str(j.next_run_time), "trigger": str(j.trigger)}
        return JsonResponse(j_json)


class ReportAPIView(APIView):
    """
        可以使用 list report 的 api 來查詢可宮製作的報表。
        使用時請傳入該報表所需的參數。 部分參數已有預設值，請參考下方說明。
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to create different reports with parameters.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d, default=start_time'),
                'carno': openapi.Schema(type=openapi.TYPE_STRING, description='車牌號碼'),
                'vid': openapi.Schema(type=openapi.TYPE_INTEGER, description='營運商id'),
                'rid': openapi.Schema(type=openapi.TYPE_INTEGER, description='路線id'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description='json/csv/html/pdf, default=json',default='json'),
                'off_duty_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間超出？秒即脫班, default=1200', default=1200),
                'early_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間提早表訂時間逾?秒鐘，視為早發, default=60', default=60),
                'delay_tol': openapi.Schema(type=openapi.TYPE_INTEGER, description='發車時間超過表訂時間逾?秒鐘，視為遲發, default=300', default=300),
            }
        )
    )
    def post(self, request, report_name):
        para_received = request.data
        para_received = format_paras(para_received)
        return parsing_post_report(request=request, rtype=report_name, para_received=para_received)


class StoptoStopReport(APIView):
    """
        可以使用 list report 的 api 來查詢可宮製作的報表。
        使用時請傳入所需的參數。 部分參數已有預設值，請參考下方說明。
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to get a route stop to stop result with parameters.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['rid'],
            properties={
                'rid': openapi.Schema(type=openapi.TYPE_INTEGER, description='路線id'),
                'date_begin': openapi.Schema(type=openapi.TYPE_STRING,
                                             description='統計起始日；format: %Y-%m-%d, default=30 days earlier',
                                             default=(datetime.today()-timedelta(days=30)).strftime("%Y-%m-%d")),
                'date_end': openapi.Schema(type=openapi.TYPE_STRING,
                                           description='統計為止日；format: %Y-%m-%d, default=today',
                                           default=(datetime.today()).strftime("%Y-%m-%d")),

                'hour_begin': openapi.Schema(type=openapi.TYPE_INTEGER,
                                             description='統計時間區間起始；0~24, default=0',
                                             default=0),
                'hour_end': openapi.Schema(type=openapi.TYPE_INTEGER,
                                           description='統計時間區間為止；0~24, default=24',
                                           default=24),

                'weekdayType': openapi.Schema(type=openapi.TYPE_ARRAY,
                                              items=openapi.Items(type=openapi.TYPE_INTEGER),
                                              description='日的種類，如：平日、假日等',
                                              default=[0, 1, 2, 3, 4, 5, 6]),
            }
        )
    )
    def post(self, request):
        sr = StopToStopResult(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
        para_received = request.data
        sr.connect()
        rp = sr.get_default_stop_to_stop_by_rid(**para_received)
        sr.disconnect()
        r = rp.to_dict("records")
        return JsonResponse(r, safe=False)



class RunsAndStoptostopCalculation(APIView):
    """
        手動API觸發演算趟次與班次
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to create different reports with parameters.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='use true to trigger'),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d, default=yesterday',
                                             default=(datetime.today()-timedelta(days=1)).strftime("%Y-%m-%d")
                                             ),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING,
                                           description='format: %Y-%m-%d, default=start_time'),
            }
        )
    )
    def post(self, request):
        d = {'start_date': None, 'end_date': None}
        para_received = request.data
        if (not ('confirm' in para_received)) or (para_received['confirm'] is not True):
            return JsonResponse({'comment': 'confirm not True'})

        if 'start_date' in para_received:
            d['start_date'] = datetime.strptime(para_received["start_date"], '%Y-%m-%d')
            if 'end_date' in para_received:
                d['end_date'] = datetime.strptime(para_received["end_date"], '%Y-%m-%d')
        results = stacking_runs_and_stoptostop(start_date=d['start_date'], end_date=d['end_date'])
        re = {}
        for i, r in enumerate(results):
            re[str(i)] = r

        return JsonResponse(re)


class DataTrafficCalculation(APIView):
    """
        手動API觸發演算資料流量
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to create different reports with parameters.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='use true to trigger'),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, description='format: %Y-%m-%d, default=yesterday',
                                             default=(datetime.today()-timedelta(days=1)).strftime("%Y-%m-%d")),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING,
                                           description='format: %Y-%m-%d, default=start_time'),
            }
        )
    )
    def post(self, request):
        d = {'start_date': None, 'end_date': None}
        para_received = request.data
        if (not ('confirm' in para_received)) or (para_received['confirm'] is not True):
            return JsonResponse({'comment': 'confirm not True'})

        if 'start_date' in para_received:
            d['start_date'] = datetime.strptime(para_received["start_date"], '%Y-%m-%d')
            if 'end_date' in para_received:
                d['end_date'] = datetime.strptime(para_received["end_date"], '%Y-%m-%d')
        results = stacking_data_traffic(start_date=d['start_date'], end_date=d['end_date'])
        re = {}
        for i, r in enumerate(results):
            re[str(i)] = r

        return JsonResponse(re)


class SetJobStatus(APIView):
    """
        手動調整背景執行工作狀態
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Use to set background Jod status.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'confirm': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='use true to trigger'),
                'action': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='action to job, pause/resume, default=none',
                                         default=None),
            }
        )
    )
    def post(self, request, job_id):
        para_received = request.data
        from core.urls import scheduler
        if para_received['action'] == 'pause':
            scheduler.pause_job(job_id)
        elif para_received['action'] == 'resume':
            scheduler.resume_job(job_id)

        j = scheduler.get_job(job_id)
        j_json = {"name": j.name, "id": j.id, "next_run_time": str(j.next_run_time), "trigger": str(j.trigger)}

        return JsonResponse(j_json)


class SentReportNotify(APIView):
    """
        重發送當日計算結果通知
    """
    def post(self, request):
        task_report_notification()
        return JsonResponse({"response":"sent"})


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
