from django.conf.urls import url
from django.urls import path
from api.views import *


urlpatterns = [
   path('list_reports/', ListReports.as_view(), name='list_reports'),
   path('list_jobs/', ListJobs.as_view(), name='list_jobs'),
   path('stoptostop_calculate/',RunsAndStoptostopCalculation.as_view(), name='stoptostop_calculate'),
   path('data_traffic_calculate/',DataTrafficCalculation.as_view(), name='data_traffic_calculate'),
   path('set_job/<str:job_id>', SetJobStatus.as_view(), name='set_job'),
   path('send_report_notify/',SentReportNotify.as_view(), name='sent_report_notify'),
   path('<str:report_name>/', ReportAPIView.as_view(), name='report_api'),

]