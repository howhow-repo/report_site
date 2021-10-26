from django.urls import path
import logging
from map.views import map_rid, map_prehandle

logger = logging.getLogger(__name__)


urlpatterns = [
    path('', map_prehandle, name='map_prehandle'),
    path('view/', map_rid, name='map_rid'),
]