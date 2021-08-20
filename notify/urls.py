# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path

from notify import views

urlpatterns = [

    # The home page
    path('', views.notify_index, name='nitify_index'),
]

