import datetime
from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)

    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class PresentacionProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='presentaciones'
    )
    nombre = models.CharField(max_length=100, help_text="Ej: Six-Pack, Pack x 24, Unidad")
    unidades = models.IntegerField(default=1, help_text="Cantidad de unidades sueltas que equivale esta presentación")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre} ({self.unidades} u.)"


class Combo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def stock_disponible(self):
        elementos = self.elementos.all()
        if not elementos.exists():
            return 0
        cantidades_posibles = []
        for elem in elementos:
            if elem.cantidad > 0:
                cantidades_posibles.append(elem.producto.stock // elem.cantidad)
        return min(cantidades_posibles) if cantidades_posibles else 0

    def __str__(self):
        return f"Combo: {self.nombre} - ${self.precio_venta}"


class ElementoCombo(models.Model):
    combo = models.ForeignKey(
        Combo,
        on_delete=models.CASCADE,
        related_name='elementos'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )
    cantidad = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} en {self.combo.nombre}"


class ConfiguracionCaja(models.Model):
    fecha_inicio_caja = models.DateField(
        default=datetime.date(2026, 6, 13),
        verbose_name="Fecha Inicio Control de Caja"
    )
    monto_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Monto o Aporte Inicial Adicional de Caja"
    )

    @classmethod
    def obtener_configuracion(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config

    def __str__(self):
        return f"Configuración de Caja (Inicio: {self.fecha_inicio_caja}, Inicial: ${self.monto_inicial})"