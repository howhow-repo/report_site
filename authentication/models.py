# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
import requests
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, request
# Create your models here.


def check_oauth(id, token) -> bool:
    if (id is None) or (token is None):
        return False
    oauth_url = "http://110.25.88.242:60004/busUser/index.php?module=User&method=is_login"
    headers = {'User-Agent': 'Mozilla/5.0'}
    payload = {'id': id, 'token': token}
    r = requests.post(oauth_url, headers=headers, data=payload)
    r = r.json()
    if r['stat'] == 'success':
        return True
    else:
        return False


def oauth_is_required(request):
    id = request.GET.get('id', None)
    token = request.GET.get('token', None)
    level = request.GET.get('level', None)
    if check_oauth(id,token):
        return False
    else:
        return True


def authcheck(request, redirect_to="/oauth_login/"):
    if request.user.is_authenticated:
        return None # Donothing
    else:
        if oauth_is_required(request=request):
            return HttpResponseRedirect(redirect_to)
        else:
            user = authenticate(username="oAuth", password="AskeyoAuth")
            login(request, user)
            return redirect("/")