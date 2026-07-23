from django import forms
from inventario.models import Producto

class NuevaVentaForm(forms.Form):

    cliente = forms.CharField(
        max_length=100,
        initial="Consumidor Final"
    )


class AgregarProductoForm(forms.Form):

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all()
    )

    cantidad = forms.IntegerField(
        min_value=1
    )