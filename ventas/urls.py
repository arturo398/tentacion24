from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_ventas, name='ventas'),
    path('nueva/', views.nueva_venta, name='nueva_venta'),
    path('<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('detalle/eliminar/<int:detalle_id>/', views.eliminar_detalle, name='eliminar_detalle'),
    path('pos/', views.pos, name='pos'),
    path('<int:venta_id>/finalizar/', views.finalizar_venta_manual, name='finalizar_venta_manual'),
    path('<int:venta_id>/eliminar/', views.eliminar_venta, name='eliminar_venta'),
    path("api/finalizar/",
        views.finalizar_venta_api,
        name="finalizar_venta_api"
    ),
    
]