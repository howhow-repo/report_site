from django.urls import path
from comparison import views


urlpatterns = [
    path('', views.comparison_index, name='comparison_index'),
    path('<str:rtype>/prehandle/', views.comparison_prehandle, name='comparison_prehandle'),
    path('<str:rtype>/result', views.comparison_result, name='comparison_result'),
]