from decimal import Decimal
from django.db import models
from inventario.models import Producto

# Create your models here.
class Compra(models.Model):
    proveedor = models.CharField(max_length=100)
    valor_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    def subtotal_productos(self):
        return sum(
            (detalle.subtotal() for detalle in self.detalles.all()),
            Decimal('0.00')
        )

    def total(self):
        return self.subtotal_productos() + Decimal(str(self.valor_envio or 0))

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor}"


class ConfiguracionCompra(models.Model):
    permitir_editar_eliminar = models.BooleanField(
        default=True,
        verbose_name="Permitir editar o eliminar compras"
    )

    @classmethod
    def obtener_configuracion(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config

    def __str__(self):
        return f"Configuración de Compras (Edición/Eliminación: {'Permitida' if self.permitir_editar_eliminar else 'Bloqueada'})"

    
class DetalleCompra(models.Model):

    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="detalles"   
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    cantidad = models.IntegerField()

    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places = 2
    )

    def subtotal(self):
        return self.cantidad * self.costo_unitario
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

@receiver(pre_save, sender=DetalleCompra)
def track_original_quantity_compras(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_cantidad = original.cantidad
        except sender.DoesNotExist:
            instance._original_cantidad = 0
    else:
        instance._original_cantidad = 0

@receiver(post_save, sender=DetalleCompra)
def adjust_stock_on_save_compras(sender, instance, created, **kwargs):
    producto = instance.producto
    if created:
        producto.stock += instance.cantidad
    else:
        original_qty = getattr(instance, '_original_cantidad', 0)
        qty_diff = instance.cantidad - original_qty
        producto.stock += qty_diff
    producto.save()

@receiver(post_delete, sender=DetalleCompra)
def adjust_stock_on_delete_compras(sender, instance, **kwargs):
    producto = instance.producto
    producto.stock -= instance.cantidad
    producto.save()
    

