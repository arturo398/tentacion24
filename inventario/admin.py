from django.contrib import admin
from .models import Producto, PresentacionProducto, Combo, ElementoCombo

class PresentacionProductoInline(admin.TabularInline):
    model = PresentacionProducto
    extra = 1

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_compra', 'precio_venta', 'stock', 'stock_minimo')
    inlines = [PresentacionProductoInline]

class ElementoComboInline(admin.TabularInline):
    model = ElementoCombo
    extra = 1

class ComboAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_venta', 'activo', 'stock_disponible')
    inlines = [ElementoComboInline]

admin.site.register(Producto, ProductoAdmin)
admin.site.register(PresentacionProducto)
admin.site.register(Combo, ComboAdmin)
admin.site.register(ElementoCombo)
