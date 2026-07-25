from decimal import Decimal
from django.db import models
from inventario.models import Producto
from django.contrib.auth.models import User
# Create your models here.

class Venta(models.Model):
    vendedor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    ]

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default='transferencia'
    )

    finalizada = models.BooleanField(
        default=False
    )
        
    cliente = models.CharField(
        max_length=100,
        default="Consumidor Final"
    )

    valor_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    def subtotal_productos(self):
        return sum(
            (detalle.subtotal() for detalle in self.detalles.all()),
            Decimal('0.00')
        )

    def total(self):
        return self.subtotal_productos() + Decimal(str(self.valor_envio or 0))
    
    def costo_total(self):
        total = Decimal('0.00')
        for detalle in self.detalles.all():
            if getattr(detalle, 'producto', None) and getattr(detalle.producto, 'precio_compra', None):
                total += Decimal(str(detalle.cantidad)) * Decimal(str(detalle.producto.precio_compra))
        return total

    def ganancia(self):
        return self.subtotal_productos() - self.costo_total()
    

    def __str__(self):
        return f"Venta #{self.id}"
    
class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    cantidad = models.IntegerField()

    precio_unitario= models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def save(self, *args, **kwargs):
        if self.venta.finalizada:
            raise ValueError("No se puede modificar ni agregar productos a una venta finalizada.")
        es_nuevo = self.pk is None
        if es_nuevo:
            if self.producto.stock < self.cantidad:
                raise ValueError(
                    f"No hay stock suficiente de {self.producto.nombre}"
                )
        else:
            try:
                original = DetalleVenta.objects.get(pk=self.pk)
                diff = self.cantidad - original.cantidad
                if diff > 0 and self.producto.stock < diff:
                    raise ValueError(
                        f"No hay stock suficiente de {self.producto.nombre} para aumentar la cantidad"
                    )
            except DetalleVenta.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.venta.finalizada:
            raise ValueError("No se puede eliminar un producto de una venta finalizada.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

@receiver(pre_save, sender=DetalleVenta)
def track_original_quantity_ventas(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_cantidad = original.cantidad
        except sender.DoesNotExist:
            instance._original_cantidad = 0
    else:
        instance._original_cantidad = 0

@receiver(post_save, sender=DetalleVenta)
def adjust_stock_on_save_ventas(sender, instance, created, **kwargs):
    producto = instance.producto
    if created:
        producto.stock -= instance.cantidad
    else:
        original_qty = getattr(instance, '_original_cantidad', 0)
        qty_diff = instance.cantidad - original_qty
        producto.stock -= qty_diff
    producto.save()

@receiver(post_delete, sender=DetalleVenta)
def adjust_stock_on_delete_ventas(sender, instance, **kwargs):
    producto = instance.producto
    producto.stock += instance.cantidad
    producto.save()
    