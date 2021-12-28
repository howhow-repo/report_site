# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path

from app import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # url with reports
    path('demo/', views.demo, name='demo'),
    path('report_index/', views.report_index, name='report_index'),
    path('report_index/testbutton/', views.test_button, name='test_button'),
    # path('report_index/pause/', views.pause_jobs, name='pause_button'),
    # path('report_index/resume/', views.resume_jobs, name='resume_button'),
    path('report_index/prehandle/', views.report_prehandle, name='report_prehandle'),
    path('report_index/<str:rtype>/', views.report_view, name='report_view'),
]

