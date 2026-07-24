from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.listar_productos, name='productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),

    # Presentaciones de productos
    path('productos/<int:producto_id>/presentaciones/', views.gestionar_presentaciones, name='gestionar_presentaciones'),
    path('presentaciones/<int:pk>/eliminar/', views.eliminar_presentacion, name='eliminar_presentacion'),

    # Combos y Promos
    path('combos/', views.listar_combos, name='combos'),
    path('combos/nuevo/', views.crear_combo, name='crear_combo'),
    path('combos/<int:pk>/editar/', views.editar_combo, name='editar_combo'),
    path('combos/<int:pk>/eliminar/', views.eliminar_combo, name='eliminar_combo'),

    path('', views.dashboard, name='dashboard'),
]