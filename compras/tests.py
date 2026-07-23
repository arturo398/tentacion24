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
