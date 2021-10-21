from django.urls import path, include, re_path
import logging
from map.views import map_index

logger = logging.getLogger(__name__)


urlpatterns = [
    path('', map_index, name='map_index'),
]