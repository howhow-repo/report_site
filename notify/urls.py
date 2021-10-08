# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path

from notify import views

urlpatterns = [

    path('', views.notify_index, name='notify_index'),
    path('add/', views.add_notify, name='add_notify'),

]
