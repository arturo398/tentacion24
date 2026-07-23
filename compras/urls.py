from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_compras, name='listar_compras'),
    path('nueva/', views.registrar_compra, name='registrar_compra'),
]
