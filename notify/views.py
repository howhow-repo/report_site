from decouple import config
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template import loader
from django.http import HttpResponse
from django.urls import reverse

from notify.form import AddNotify
from notify.models import LineNotifyControl, add_notify_user

# Create your views here.
CONTEXT = {
    "PROJECT_TITLE": config('PROJECT_TITLE', default='unnamed')
}


@login_required(login_url="/login/")
def notify_index(request):
    context = {**CONTEXT, **{'segment': 'notify'}}
    load_template = 'notify/notify_index.html'
    members = LineNotifyControl.objects.all()
    ms = []
    for m in members:
        ms.append({"name": m.name, "token": m.token.replace(m.token[:-10], "**********"), "activate": m.activate})

    context['members'] = ms
    context['AddNotify'] = AddNotify

    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def add_notify(request):
    add_user = AddNotify(request.POST)
    if add_user.is_valid():
        add_notify_user(name=add_user.cleaned_data['name'],
                        token=add_user.cleaned_data['token'],
                        activate=add_user.cleaned_data['activate'])

    return redirect(reverse('notify_index'))
