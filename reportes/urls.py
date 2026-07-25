from django.urls import path
from . import views

urlpatterns = [
    path('', views.reportes, name='reportes'),
    path('pdf/', views.generar_pdf_reporte, name='generar_pdf_reporte'),
]