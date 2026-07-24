from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.listar_productos, name='productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),

    path('', views.dashboard, name='dashboard'),
]