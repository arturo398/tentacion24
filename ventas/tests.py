from django.test import TestCase
from inventario.models import Producto
from ventas.models import Venta, DetalleVenta
from django.contrib.auth.models import User

class StockControlSignalsTest(TestCase):
    def setUp(self):
        # Create a test product
        self.producto = Producto.objects.create(
            nombre="Test Product",
            categoria="Test",
            precio_compra=10.00,
            precio_venta=15.00,
            stock=10,
            stock_minimo=2
        )
        # Create a user and a sale
        self.vendedor = User.objects.create_user(username="vendedor", password="testpassword")
        self.venta = Venta.objects.create(cliente="Test Client", vendedor=self.vendedor)

    def test_create_detalle_venta_deducts_stock(self):
        # Creating detail should deduct stock
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=3,
            precio_unitario=self.producto.precio_venta
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)

    def test_delete_detalle_venta_restores_stock(self):
        detalle = DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=3,
            precio_unitario=self.producto.precio_venta
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)
        
        # Deleting should restore stock
        detalle.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_update_detalle_venta_quantity_adjusts_stock(self):
        detalle = DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=3,
            precio_unitario=self.producto.precio_venta
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)
        
        # Increasing quantity by 2
        detalle.cantidad = 5
        detalle.save()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

        # Decreasing quantity by 4
        detalle.cantidad = 1
        detalle.save()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 9)

    def test_insufficient_stock_raises_value_error(self):
        with self.assertRaises(ValueError):
            DetalleVenta.objects.create(
                venta=self.venta,
                producto=self.producto,
                cantidad=15, # more than available stock (10)
                precio_unitario=self.producto.precio_venta
            )

from django.urls import reverse

class VentaFinalizacionTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Test Product",
            categoria="Test",
            precio_compra=10.00,
            precio_venta=15.00,
            stock=10,
            stock_minimo=2
        )
        self.vendedor = User.objects.create_user(username="vendedor", password="testpassword")
        self.client.login(username="vendedor", password="testpassword")
        self.venta = Venta.objects.create(cliente="Test Client", vendedor=self.vendedor, finalizada=False)
        self.detalle = DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio_venta
        )

    def test_finalizar_venta_manual_locks_sale(self):
        # Finalize sale
        response = self.client.get(reverse('finalizar_venta_manual', args=[self.venta.id]))
        self.venta.refresh_from_db()
        self.assertTrue(self.venta.finalizada)

        # Try to delete detail (should fail and redirect without deleting)
        response_delete = self.client.get(reverse('eliminar_detalle', args=[self.detalle.id]))
        self.assertEqual(DetalleVenta.objects.count(), 1) # Not deleted!

        # Try to add product via POST
        response_add = self.client.post(reverse('detalle_venta', args=[self.venta.id]), {
            'producto': self.producto.id,
            'cantidad': 1
        })
        self.assertEqual(DetalleVenta.objects.filter(venta=self.venta).count(), 1) # Not added!

    def test_eliminar_venta_restores_stock(self):
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)

        # Delete whole sale
        response = self.client.get(reverse('eliminar_venta', args=[self.venta.id]))
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(DetalleVenta.objects.count(), 0)

        # Product stock should be restored to 10
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)


class VentaModelRestriccionesTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Test Product",
            categoria="Test",
            precio_compra=10.00,
            precio_venta=15.00,
            stock=10,
            stock_minimo=2
        )
        self.vendedor = User.objects.create_user(username="vendedor", password="testpassword")
        self.venta = Venta.objects.create(cliente="Test Client", vendedor=self.vendedor, finalizada=False)
        self.detalle = DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio_venta
        )
        # Finalize the sale
        self.venta.finalizada = True
        self.venta.save()

    def test_save_on_finalized_sale_raises_value_error(self):
        # Trying to update quantity of an existing detail on a finalized sale
        self.detalle.cantidad = 3
        with self.assertRaises(ValueError):
            self.detalle.save()

    def test_delete_on_finalized_sale_raises_value_error(self):
        # Trying to delete a detail on a finalized sale
        with self.assertRaises(ValueError):
            self.detalle.delete()

    def test_create_on_finalized_sale_raises_value_error(self):
        # Trying to create a new detail on a finalized sale
        with self.assertRaises(ValueError):
            DetalleVenta.objects.create(
                venta=self.venta,
                producto=self.producto,
                cantidad=1,
                precio_unitario=self.producto.precio_venta
            )

    def test_cascade_delete_works_on_finalized_sale(self):
        # Deleting the sale itself should work even if finalized (cascade delete)
        self.venta.delete()
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(DetalleVenta.objects.count(), 0)
        
        # Stock should be restored
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_venta_total_and_ganancia_with_valor_envio(self):
        from decimal import Decimal
        venta_envio = Venta.objects.create(cliente="Cliente Test", valor_envio=25.00)
        DetalleVenta.objects.create(
            venta=venta_envio,
            producto=self.producto,
            cantidad=2,
            precio_unitario=15.00
        )
        # Subtotal productos: 2 * 15 = 30. Total Venta = 30 + 25 = 55.
        # Costo productos = 2 * 10 = 20. Ganancia Neta (excluyendo envío tercerizado) = 30 - 20 = 10.
        self.assertEqual(venta_envio.subtotal_productos(), Decimal('30.00'))
        self.assertEqual(venta_envio.total(), Decimal('55.00'))
        self.assertEqual(venta_envio.costo_total(), Decimal('20.00'))
        self.assertEqual(venta_envio.ganancia(), Decimal('10.00'))

