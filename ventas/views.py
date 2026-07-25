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
    from inventario.models import Combo
    productos = Producto.objects.all().prefetch_related('presentaciones')
    combos = Combo.objects.filter(activo=True).prefetch_related('elementos__producto')
    categorias = list(Producto.objects.values_list('categoria', flat=True).distinct())

    return render(
        request,
        'ventas/pos.html',
        {
            'productos': productos,
            'combos': combos,
            'categorias': categorias
        }
    )

@csrf_exempt
@require_POST
@login_required
def finalizar_venta_api(request):
    from inventario.models import Combo, PresentacionProducto
    try:
        datos = json.loads(request.body)
        cliente = datos.get("cliente", "Consumidor Final")
        metodo_pago = datos.get("metodo_pago", "transferencia")
        valor_envio = float(datos.get("valor_envio", 0))
        items = datos.get("productos", [])

        if not items:
            return JsonResponse({"ok": False, "error": "El carrito está vacío."}, status=400)

        stock_actualizado = {}

        with transaction.atomic():
            venta = Venta.objects.create(
                cliente=cliente,
                vendedor=request.user,
                metodo_pago=metodo_pago,
                valor_envio=valor_envio,
                finalizada=False
            )

            for item in items:
                es_combo = item.get("es_combo", False)

                if es_combo:
                    combo_id = item.get("id")
                    combo = Combo.objects.get(id=combo_id)
                    cant_combos = int(item.get("cantidad", 1))
                    precio_combo = float(item.get("precio", combo.precio_venta))

                    # Para cada componente del combo, registramos un detalle proporcional o se deduce el stock
                    elementos = combo.elementos.all()
                    for elem in elementos:
                        cant_descuento = elem.cantidad * cant_combos
                        # Calculamos costo/precio asignado
                        precio_unitario_elem = (precio_combo / elementos.count()) / elem.cantidad if elem.cantidad > 0 else 0
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=elem.producto,
                            cantidad=cant_descuento,
                            precio_unitario=precio_unitario_elem
                        )
                        elem.producto.refresh_from_db()
                        stock_actualizado[elem.producto.id] = elem.producto.stock
                else:
                    prod_id = item.get("id")
                    producto = Producto.objects.get(id=prod_id)
                    cant_comprada = int(item.get("cantidad", 1))
                    unidades_por_pack = int(item.get("unidades_pack", 1))
                    precio_total_item = float(item.get("precio", producto.precio_venta))

                    unidades_totales_descuento = cant_comprada * unidades_por_pack
                    precio_unitario_lata = precio_total_item / unidades_por_pack if unidades_por_pack > 0 else float(producto.precio_venta)

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=unidades_totales_descuento,
                        precio_unitario=precio_unitario_lata
                    )

                    producto.refresh_from_db()
                    stock_actualizado[producto.id] = producto.stock

            venta.finalizada = True
            venta.save()

            # Formatear lista de stock actualizado
            lista_stock = [{"id": k, "stock": v} for k, v in stock_actualizado.items()]

        return JsonResponse({
            "ok": True,
            "venta": venta.id,
            "stock_actualizado": lista_stock
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=400)