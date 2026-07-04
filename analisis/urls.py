from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('mm1/', views.mm1, name='mm1'),
    path('mmc/', views.mmc, name='mmc'),
    path('analisis/', views.analisis, name='analisis'),
    path('cargar/', views.cargar, name='cargar'),
]
