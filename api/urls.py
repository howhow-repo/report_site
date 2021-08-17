from django.conf.urls import url
from django.urls import path
from api.views import ReportAPIView,ListReports



urlpatterns = [
   path('list_report/', ListReports.as_view(), name='list_reports'),
   path('<str:report_name>/', ReportAPIView.as_view(), name='report_api')
]