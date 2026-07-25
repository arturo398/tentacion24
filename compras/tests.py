from decimal import Decimal
from django.test import TestCase
from inventario.models import Producto
from compras.models import Compra, DetalleCompra

class PurchaseStockControlTest(TestCase):
    def setUp(self):
        # Create a test product
        self.producto = Producto.objects.create(
            nombre="Test Insumo",
            categoria="Insumos",
            precio_compra=5.00,
            precio_venta=10.00,
            stock=10,
            stock_minimo=2
        )
        self.compra = Compra.objects.create(proveedor="Proveedor Test")

    def test_create_detalle_compra_increases_stock(self):
        DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            costo_unitario=self.producto.precio_compra
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)

    def test_delete_detalle_compra_decreases_stock(self):
        detalle = DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            costo_unitario=self.producto.precio_compra
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)

        detalle.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_update_detalle_compra_quantity_adjusts_stock(self):
        detalle = DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            costo_unitario=self.producto.precio_compra
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)

        # Increase quantity by 3
        detalle.cantidad = 8
        detalle.save()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 18)

        # Decrease quantity by 6
        detalle.cantidad = 2
        detalle.save()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 12)

    def test_compra_total_includes_valor_envio(self):
        compra_envio = Compra.objects.create(proveedor="Proveedor Envío", valor_envio=50.00)
        DetalleCompra.objects.create(
            compra=compra_envio,
            producto=self.producto,
            cantidad=2,
            costo_unitario=5.00
        )
        # Subtotal: 2 * 5 = 10, Envío: 50, Total = 60
        self.assertEqual(compra_envio.subtotal_productos(), Decimal('10.00'))
        self.assertEqual(compra_envio.total(), Decimal('60.00'))

    def test_configuracion_compra_toggle(self):
        from compras.models import ConfiguracionCompra
        config = ConfiguracionCompra.obtener_configuracion()
        self.assertTrue(config.permitir_editar_eliminar)

        config.permitir_editar_eliminar = False
        config.save()

        config_reload = ConfiguracionCompra.obtener_configuracion()
        self.assertFalse(config_reload.permitir_editar_eliminar)

