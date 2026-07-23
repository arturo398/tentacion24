from django.urls import path
from . import views

urlpatterns = [
    path(
        'productos/',
        views.listar_productos,
        name='productos'
    ),

    path('', views.dashboard, name='dashboard'),
    
]