from django.contrib import admin
from .models import Venta, DetalleVenta


# Register your models here.
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.finalizada:
            return ['producto', 'cantidad', 'precio_unitario']
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.finalizada:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.finalizada:
            return False
        return super().has_delete_permission(request, obj)
    
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = [
        DetalleVentaInline
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.finalizada:
            return ['vendedor', 'metodo_pago', 'finalizada', 'cliente']
        return super().get_readonly_fields(request, obj)

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.venta.finalizada:
            return ['venta', 'producto', 'cantidad', 'precio_unitario']
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.venta.finalizada:
            return False
        return super().has_delete_permission(request, obj)