from django import forms
from .models import Producto, PresentacionProducto, Combo, ElementoCombo

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio_compra', 'precio_venta', 'stock', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cerveza Brahva 473ml'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cervezas'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'}),
        }


class PresentacionProductoForm(forms.ModelForm):
    class Meta:
        model = PresentacionProducto
        fields = ['nombre', 'unidades', 'precio_venta']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Six-Pack, Pack x 24'}),
            'unidades': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ej: 6'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej: 7500.00'}),
        }


class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = ['nombre', 'descripcion', 'precio_venta', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Promo Fernet + 2 Cocas'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción del combo'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '12000.00'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
