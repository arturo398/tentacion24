import json
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from inventario.models import Producto
from .models import Venta, DetalleVenta
from .forms import NuevaVentaForm, AgregarProductoForm


@login_required
def listar_ventas(request):
    if request.user.is_superuser:

        ventas = Venta.objects.order_by('-fecha')

    else:

        ventas = Venta.objects.filter(
            vendedor=request.user
        ).order_by('-fecha')
    
    return render(request, 'ventas/listar_ventas.html', {'ventas': ventas})

@login_required
def detalle_venta(request, venta_id):

    venta = get_object_or_404(
        Venta,
        id=venta_id
    )
    #control de permisos
    if not request.user.is_superuser and venta.vendedor != request.user:

        messages.error(
            request,
            "No tienes permiso para ver esta venta."
        )

        return redirect('ventas')
        



    if request.method == 'POST':
        if venta.finalizada:
            messages.error(
                request,
                'No se pueden agregar productos a una venta finalizada.'
            )
            return redirect(
                'detalle_venta',
                venta_id=venta.id
            )

        form = AgregarProductoForm(
            request.POST
        )

        if form.is_valid():

            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']

            try:

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta
                )

                messages.success(
                    request,
                    "Producto agregado."
                )

            except ValueError as e:

                messages.error(
                    request,
                    str(e)
                )

        return redirect(
            'detalle_venta',
            venta_id=venta.id
        )

    form = AgregarProductoForm()

    return render(
        request,
        'ventas/detalle_venta.html',
        {
            'venta': venta,
            'form': form
        }
    )

@login_required
def nueva_venta(request):
    return redirect('pos')

@login_required
def eliminar_detalle(request, detalle_id):

    detalle = get_object_or_404(
        DetalleVenta,
        id=detalle_id
    )
    if detalle.venta.finalizada:
        messages.error(
            request,
            'No se pueden eliminar productos de una venta finalizada.'
        )
        return redirect(
            'detalle_venta',
            venta_id=detalle.venta.id
        )

    venta_id = detalle.venta.id

    detalle.delete()

    messages.success(
        request,
        "Producto eliminado de la venta."
    )

    return redirect(
        'detalle_venta',
        venta_id=venta_id
    )



@login_required
def finalizar_venta_manual(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    if not venta.detalles.exists():
        messages.error(
            request,
            'No se puede finalizar una venta sin productos.'
        )
    else:
        venta.finalizada = True
        venta.save()
        messages.success(
            request,
            'Venta finalizada correctamente.'
        )
    return redirect('detalle_venta', venta_id=venta.id)

@login_required
def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
    messages.success(
        request,
        'Venta eliminada correctamente y el stock ha sido devuelto.'
    )
    return redirect('ventas')

@login_required
def pos(request):
    productos = Producto.objects.all()
    categorias = Producto.objects.values_list('categoria', flat=True).distinct()
    return render(
        request,
        'ventas/pos.html',
        {
            'productos': productos,
            'categorias': categorias
        }
    )

@csrf_exempt
@require_POST
@login_required
def finalizar_venta_api(request):

    try:
        datos = json.loads(request.body)
        cliente = datos.get(
            "cliente",
            "Consumidor Final"
        )
        metodo_pago = datos.get("metodo_pago", "transferencia")

        productos  = datos.get(
            "productos", 
            []
        )

        stock_actualizado = []

        with transaction.atomic():

            # Crea la venta como borrador primero para permitir agregar los detalles
            venta = Venta.objects.create(
                cliente=cliente,
                vendedor=request.user,
                metodo_pago=metodo_pago,
                finalizada=False
            )

            for item in productos:

                producto = Producto.objects.get(
                    id=item["id"]
                )

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=item["cantidad"],
                    precio_unitario=producto.precio_venta
                )

                producto.refresh_from_db()

                stock_actualizado.append({
                    "id": producto.id,
                    "stock": producto.stock
                })

            # Finaliza la venta una vez cargados todos los productos
            venta.finalizada = True
            venta.save()

        return JsonResponse({
            "ok": True,
            "venta": venta.id,
            "stock_actualizado": stock_actualizado
        })
    
    except Exception as e:
        
        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=400)