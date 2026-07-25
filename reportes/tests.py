from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class ReportesViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_reportes',
            email='admin@test.com',
            password='password123'
        )

    def test_reportes_view_accessible_by_admin(self):
        self.client.login(username='admin_reportes', password='password123')
        response = self.client.get(reverse('reportes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('facturacion_semana', response.context)
        self.assertIn('ganancia_semana', response.context)
        self.assertIn('cantidad_ventas_semana', response.context)

    def test_generar_pdf_reporte_semanal_returns_pdf(self):
        self.client.login(username='admin_reportes', password='password123')
        response = self.client.get(reverse('generar_pdf_reporte') + '?tipo=semanal')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue('reporte_semanal_tentacion24_' in response['Content-Disposition'])

    def test_generar_pdf_reporte_mensual_returns_pdf(self):
        self.client.login(username='admin_reportes', password='password123')
        response = self.client.get(reverse('generar_pdf_reporte') + '?tipo=mensual')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue('reporte_mensual_tentacion24_' in response['Content-Disposition'])

