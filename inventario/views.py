from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Producto, PresentacionProducto, Combo, ElementoCombo
from .forms import ProductoForm, PresentacionProductoForm, ComboForm
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
    productos = Producto.objects.all().order_by('nombre').prefetch_related('presentaciones')

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
    if not request.user.is_superuser:
        messages.error(request, "Se requieren permisos de administrador para crear productos.")
        return redirect('productos')
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
    if not request.user.is_superuser:
        messages.error(request, "Se requieren permisos de administrador para editar productos.")
        return redirect('productos')
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
    if not request.user.is_superuser:
        messages.error(request, "Se requieren permisos de administrador para eliminar productos.")
        return redirect('productos')
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
    return redirect('productos')


# --- PRESENTACIONES DE PRODUCTOS ---
@login_required
def gestionar_presentaciones(request, producto_id):
    if not request.user.is_superuser:
        messages.error(request, "Se requieren permisos de administrador para gestionar packs/presentaciones.")
        return redirect('productos')
    producto = get_object_or_404(Producto, pk=pk if 'pk' in locals() else producto_id)
    presentaciones = producto.presentaciones.all()

    if request.method == 'POST':
        form = PresentacionProductoForm(request.POST)
        if form.is_valid():
            presentacion = form.save(commit=False)
            presentacion.producto = producto
            presentacion.save()
            messages.success(request, f'Presentación "{presentacion.nombre}" agregada a {producto.nombre}.')
            return redirect('gestionar_presentaciones', producto_id=producto.id)
    else:
        form = PresentacionProductoForm()

    return render(request, 'inventario/presentaciones.html', {
        'producto': producto,
        'presentaciones': presentaciones,
        'form': form
    })



@login_required
def eliminar_presentacion(request, pk):
    presentacion = get_object_or_404(PresentacionProducto, pk=pk)
    producto_id = presentacion.producto.id
    if request.method == 'POST':
        nombre = presentacion.nombre
        presentacion.delete()
        messages.success(request, f'Presentación "{nombre}" eliminada.')
    return redirect('gestionar_presentaciones', producto_id=producto_id)


# --- COMBOS Y PROMOS ---
@login_required
def listar_combos(request):
    combos = Combo.objects.all().prefetch_related('elementos__producto').order_by('-fecha_creacion')
    return render(request, 'inventario/combos.html', {'combos': combos})


@login_required
def crear_combo(request):
    productos = Producto.objects.all().order_by('nombre')
    if request.method == 'POST':
        form = ComboForm(request.POST)
        prod_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        if form.is_valid():
            if not prod_ids:
                messages.error(request, "Debe agregar al menos un producto al combo.")
            else:
                with transaction.atomic():
                    combo = form.save()
                    for pid, cant in zip(prod_ids, cantidades):
                        if pid and int(cant) > 0:
                            prod = Producto.objects.get(id=pid)
                            ElementoCombo.objects.create(
                                combo=combo,
                                producto=prod,
                                cantidad=int(cant)
                            )
                    messages.success(request, f'Combo "{combo.nombre}" creado con éxito.')
                    return redirect('combos')
    else:
        form = ComboForm()

    return render(request, 'inventario/combo_form.html', {
        'form': form,
        'productos': productos,
        'titulo': 'Nuevo Combo / Promo'
    })


@login_required
def editar_combo(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    productos = Producto.objects.all().order_by('nombre')
    elementos = combo.elementos.all()

    if request.method == 'POST':
        form = ComboForm(request.POST, instance=combo)
        prod_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        if form.is_valid():
            if not prod_ids:
                messages.error(request, "Debe agregar al menos un producto al combo.")
            else:
                with transaction.atomic():
                    combo = form.save()
                    combo.elementos.all().delete()
                    for pid, cant in zip(prod_ids, cantidades):
                        if pid and int(cant) > 0:
                            prod = Producto.objects.get(id=pid)
                            ElementoCombo.objects.create(
                                combo=combo,
                                producto=prod,
                                cantidad=int(cant)
                            )
                    messages.success(request, f'Combo "{combo.nombre}" actualizado correctamente.')
                    return redirect('combos')
    else:
        form = ComboForm(instance=combo)

    return render(request, 'inventario/combo_form.html', {
        'form': form,
        'combo': combo,
        'productos': productos,
        'elementos': elementos,
        'titulo': f'Editar Combo: {combo.nombre}'
    })


@login_required
def eliminar_combo(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    if request.method == 'POST':
        nombre = combo.nombre
        combo.delete()
        messages.success(request, f'Combo "{nombre}" eliminado.')
    return redirect('combos')


@login_required
def dashboard(request):
    total_productos = Producto.objects.count()
    stock_bajo = Producto.objects.filter(stock__lte=F('stock_minimo')).count()
    productos_stock_bajo = Producto.objects.filter(stock__lte=F('stock_minimo'))
    total_ventas = Venta.objects.count()
    total_compras = Compra.objects.count()
    ventas = Venta.objects.all()
    compras = Compra.objects.all()

    facturacion_total = sum(venta.total() for venta in ventas)
    ganancia_total = sum(venta.ganancia() for venta in ventas)
    compras_total_monetario = sum(compra.total() for compra in compras)
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

    return render(request, 'inventario/dashboard.html', contexto)