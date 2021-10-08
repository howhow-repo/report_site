from django.urls import path
from stoptostop_analysis import views


urlpatterns = [
   path('prehandle/', views.stoptostop_prehandle, name='stoptostop_prehandle'),
   path('traveltime_result/', views.stoptostop_traveltime_view, name='stoptostop_traveltime_result'),
   path('traveltime_result/<int:rsid>', views.stoptostop_traveltime_hourly, name='stoptostop_traveltime_hourly'),
   path('staytime_result/', views.stoptostop_staytime_view, name='stoptostop_staytime_result'),
   path('staytime_result/<int:rsid>', views.stoptostop_staytime_hourly, name='stoptostop_staytime_hourly'),
]