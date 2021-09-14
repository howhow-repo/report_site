from django.conf.urls import url
from django.urls import path
from data_traffic import views


urlpatterns = [
   path('prehandle/', views.data_traffic_prehandle, name='data_traffic_prehandle'),
   path('result/', views.data_traffic_view, name='data_traffic_view'),
]