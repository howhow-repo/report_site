from django.conf.urls import url
from django.urls import path
from api.views import *


urlpatterns = [
   path('list_reports/', ListReports.as_view(), name='list_reports'),
   path('list_jobs/', ListJobs.as_view(), name='list_jobs'),
   path('calculate/',RunsAndStoptostopCalculation.as_view(), name='stoptostop'),
   path('set_job/<str:job_id>',setJobStatus.as_view(), name='set_job'),
   path('<str:report_name>/', ReportAPIView.as_view(), name='report_api')
]