from django.urls import path
from comparison import views


urlpatterns = [
    path('', views.comparison_index, name='comparison_index'),
    path('prehandle/<str:rtype>/', views.comparison_prehandle, name='comparison_prehandle'),
]