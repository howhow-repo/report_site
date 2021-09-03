from django.conf.urls import url
from django.urls import path
from bus_rawdata import views


urlpatterns = [
   path('prehandle/', views.bus_rawdata_prehandle, name='bus_rawdata_prehandle'),
   path('result/', views.bus_rawdata_view, name='bus_rawdata_view'),
]