from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from notify.models import LineNotifyControl

# Create your views here.


@login_required(login_url="/login/")
def notify_index(request):
    context = {'segment': 'notify'}
    load_template = 'notify/notify_index.html'
    members = LineNotifyControl.objects.all()
    ms = []
    for m in members:
        ms.append({"name":m.name, "token": m.token.replace(m.token[:-10], "**********"), "activate": m.activate})

    context['members'] = ms
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))