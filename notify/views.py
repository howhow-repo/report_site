from decouple import config
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from notify.models import LineNotifyControl

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
        ms.append({"name":m.name, "token": m.token.replace(m.token[:-10], "**********"), "activate": m.activate})

    context['members'] = ms
    html_template = loader.get_template(load_template)
    return HttpResponse(html_template.render(context, request))