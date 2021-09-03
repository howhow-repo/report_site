# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging

import django.db.utils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.contrib import admin
from django.urls import path, include, re_path
from django_apscheduler.jobstores import DjangoJobStore
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from app.tasks import sql_conn_keepalive, stacking_runs_and_stoptostop, task_report_notification
from app.views import pages
from .tasks import delete_old_job_executions

logger = logging.getLogger(__name__)

schema_view = get_schema_view(
    openapi.Info(
        title="公車報表 API",
        default_version='v1',
        description="以API撈取報表，可回傳json/csv/html/pdf",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin route
    path("", include("authentication.urls")),  # Auth routes - login / register
    path("", include("app.urls")),  # UI Kits Html files
    path("notify/", include("notify.urls")),
    path("stoptostop/", include("stoptostop_analysis.urls")),
    path("bus_rawdata/", include("bus_rawdata.urls")),
    path("api/", include("api.urls")),  # for restful & swagger
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Matches any html file
    re_path(r'^.*\.*', pages, name='pages'),
]

# Daily or scheduled job are submit here
try:
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        sql_conn_keepalive,
        trigger=CronTrigger(
            minute="30"
        ),
        id="sql_conn_keepalive",
        max_instances=1,
        misfire_grace_time=30,
        replace_existing=True,
    )

    scheduler.add_job(
        stacking_runs_and_stoptostop,
        trigger=CronTrigger(
            hour="03", minute="30"
        ),
        id="stacking_runs_and_stoptostop",
        max_instances=1,
        misfire_grace_time=3600,
        replace_existing=True,
    )

    scheduler.add_job(
        task_report_notification,
        trigger=CronTrigger(
            hour="04", minute="00"
        ),
        id="task_report_notification",
        max_instances=1,
        misfire_grace_time=3600,
        replace_existing=True,
    )

    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(
            day_of_week="mon", hour="00", minute="00"
        ),  # Midnight on Monday, before start of the next work week.
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )

    try:
        scheduler.start()
        logger.info('Starting apscheduler')
    except KeyboardInterrupt:
        scheduler.shutdown()
    ###

except django.db.utils.ProgrammingError:
    pass