# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path

from notify import views

urlpatterns = [

    # The home page
    path('', views.notify_index, name='notify_index'),
]
