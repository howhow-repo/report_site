from django.conf.urls import url
from django.urls import path
from stoptostop_analysis import views


urlpatterns = [
   path('prehandle/', views.stoptostop_prehandle, name='stoptostop_prehandle'),
   path('result/', views.stoptostop_view, name='stoptostop_result'),
   path('result/<int:rsid>', views.stoptostop_hourly, name='stoptostop_hourly'),
]