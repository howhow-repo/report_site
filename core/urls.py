# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from django.contrib import admin
from django.urls import path, include
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

from apscheduler.triggers.cron import CronTrigger
from .tasks import delete_old_job_executions
from app.tasks import test, stacking_runs_and_stoptostop

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin route
    path("", include("authentication.urls")),  # Auth routes - login / register
    path("", include("app.urls")),  # UI Kits Html files
]


# Daily or scheduled job are submit here
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

scheduler.add_job(
    test,
    trigger=CronTrigger(
        second="5"  #
    ),
    id="test",  # The `id` assigned to each job MUST be unique
    max_instances=1,
    replace_existing=True,
)

scheduler.add_job(
    stacking_runs_and_stoptostop,
    trigger=CronTrigger(
        hour="03", minute="30"  #
    ),
    id="runsAndStopStacking",  # The `id` assigned to each job MUST be unique
    max_instances=1,
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
except KeyboardInterrupt:
    scheduler.shutdown()
###
