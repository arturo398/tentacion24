from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_compras, name='listar_compras'),
    path('nueva/', views.registrar_compra, name='registrar_compra'),
    path('toggle-permiso/', views.toggle_permiso_compra, name='toggle_permiso_compra'),
    path('<int:compra_id>/editar/', views.editar_compra, name='editar_compra'),
    path('<int:compra_id>/eliminar/', views.eliminar_compra, name='eliminar_compra'),
    path('api/crear-producto/', views.crear_producto_ajax, name='crear_producto_ajax'),
]


