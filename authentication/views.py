# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from decouple import config
import requests

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template import loader

from .forms import LoginForm, SignUpForm


CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
}


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:    
                msg = 'Invalid credentials'    
        else:
            msg = 'Error validating the form'    

    return render(request, "accounts/login.html", {**CONTEXT, **{"form": form, "msg": msg}})


def oauth_login_view(request):
    return HttpResponseRedirect(f"http://110.25.88.242:60004/bus/?reurl=http://{config('SERVER', default='127.0.0.1')}:{config('SERVER_PORT', default='8000')}/")


def register_user(request):
    html_template = loader.get_template('page-404.html')
    return HttpResponseNotFound(html_template.render({}, request))

    # msg     = None
    # success = False
    #
    # if request.method == "POST":
    #     form = SignUpForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         username = form.cleaned_data.get("username")
    #         raw_password = form.cleaned_data.get("password1")
    #         user = authenticate(username=username, password=raw_password)
    #
    #         msg     = 'User created - please <a href="/login">login</a>.'
    #         success = True
    #
    #         #return redirect("/login/")
    #
    #     else:
    #         msg = 'Form is not valid'
    # else:
    #     form = SignUpForm()
    #
    # return render(request, "accounts/register.html", {**CONTEXT, **{"form": form, "msg": msg, "success": success}})


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