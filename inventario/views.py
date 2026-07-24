from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm
from compras.models import Compra
from ventas.models import Venta
from django.db.models import Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import json

def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


@login_required
def listar_productos(request):
    busqueda = request.GET.get('q', '')
    productos = Producto.objects.all().order_by('nombre')

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(categoria__icontains=busqueda)
        )

    return render(
        request,
        'inventario/productos.html',
        {
            'productos': productos,
            'busqueda': busqueda
        }
    )


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('productos')
    else:
        form = ProductoForm()

    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'titulo': 'Nuevo Producto'
    })


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'titulo': f'Editar Producto: {producto.nombre}',
        'producto': producto
    })


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
    return redirect('productos')


def dashboard(request):

    total_productos = Producto.objects.count()

    stock_bajo = Producto.objects.filter(
        stock__lte=F('stock_minimo')
    ).count()

    productos_stock_bajo = Producto.objects.filter(
        stock__lte=F('stock_minimo')
    )
    

    total_ventas = Venta.objects.count()

    total_compras = Compra.objects.count()

    ventas = Venta.objects.all()
    compras = Compra.objects.all()

    facturacion_total = sum(
        venta.total() for venta in ventas
    )

    ganancia_total = sum(venta.ganancia() for venta in ventas)

    compras_total_monetario = sum(
        compra.total() for compra in compras
    )

    ultimas_ventas = Venta.objects.order_by('-fecha')[:5]

    contexto = {
        'total_productos': total_productos,
        'stock_bajo': stock_bajo,
        'productos_stock_bajo': productos_stock_bajo,
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'ultimas_ventas': ultimas_ventas,
        'facturacion_total': facturacion_total,
        'ganancia_total': ganancia_total,
        'compras_total_monetario': compras_total_monetario
    } 

    return render(
        request,
        'inventario/dashboard.html',
        contexto
    )