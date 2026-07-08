from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('cola/', views.cola, name='cola'),
    path('calculo/', views.calculo, name='calculo'),
    path('analisis/', views.analisis, name='analisis'),
]
