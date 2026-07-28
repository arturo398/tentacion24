from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Compra, DetalleCompra, ConfiguracionCompra
from inventario.models import Producto
from django.http import JsonResponse
from django.db import transaction
import json

@login_required
def listar_compras(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a Compras.")
        return redirect('productos')

    busqueda = request.GET.get('q', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    queryset = Compra.objects.prefetch_related('detalles__producto').order_by('-fecha')

    if busqueda:
        queryset = queryset.filter(proveedor__icontains=busqueda)

    if fecha_inicio:
        queryset = queryset.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin:
        queryset = queryset.filter(fecha__date__lte=fecha_fin)

    config = ConfiguracionCompra.obtener_configuracion()
    return render(request, 'compras/listar_compras.html', {
        'compras': queryset,
        'config': config,
        'busqueda': busqueda,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    })

@login_required
def toggle_permiso_compra(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para modificar esta configuración.")
        return redirect('listar_compras')

    if request.method == 'POST':
        config = ConfiguracionCompra.obtener_configuracion()
        config.permitir_editar_eliminar = not config.permitir_editar_eliminar
        config.save()
        estado = "activado" if config.permitir_editar_eliminar else "desactivado"
        messages.success(request, f"El permiso para editar/eliminar compras ha sido {estado}.")

    return redirect('listar_compras')

@login_required
def registrar_compra(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para registrar Compras.")
        return redirect('productos')

    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            proveedor = datos.get("proveedor", "Proveedor").strip()
            if not proveedor:
                proveedor = "Proveedor Desconocido"
            valor_envio = float(datos.get("valor_envio", 0))
            productos = datos.get("productos", [])

            if not productos:
                return JsonResponse({"ok": False, "error": "Debe agregar al menos un producto"}, status=400)

            with transaction.atomic():
                compra = Compra.objects.create(
                    proveedor=proveedor,
                    valor_envio=valor_envio
                )
                for item in productos:
                    producto = Producto.objects.get(id=item["id"])
                    cantidad = int(item["cantidad"])
                    costo_unitario = float(item["costo_unitario"])
                    if costo_unitario > 0:
                        producto.precio_compra = costo_unitario
                        producto.save()
                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        costo_unitario=costo_unitario
                    )
            return JsonResponse({"ok": True, "compra_id": compra.id})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'compras/registrar_compra.html', {'productos': productos})

@login_required
def eliminar_compra(request, compra_id):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para eliminar compras.")
        return redirect('listar_compras')

    config = ConfiguracionCompra.obtener_configuracion()
    if not config.permitir_editar_eliminar:
        messages.error(request, "La edición y eliminación de compras está desactivada en la configuración.")
        return redirect('listar_compras')

    compra = get_object_or_404(Compra, id=compra_id)
    with transaction.atomic():
        compra.delete()
    messages.success(request, f"Compra #{compra_id} eliminada correctamente. El stock asociado ha sido descontado.")
    return redirect('listar_compras')

@login_required
def editar_compra(request, compra_id):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar compras.")
        return redirect('listar_compras')

    config = ConfiguracionCompra.obtener_configuracion()
    if not config.permitir_editar_eliminar:
        messages.error(request, "La edición y eliminación de compras está desactivada en la configuración.")
        return redirect('listar_compras')

    compra = get_object_or_404(Compra, id=compra_id)

    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            proveedor = datos.get("proveedor", "").strip() or "Proveedor Desconocido"
            valor_envio = float(datos.get("valor_envio", 0))
            productos = datos.get("productos", [])

            if not productos:
                return JsonResponse({"ok": False, "error": "Debe haber al menos un producto en la compra."}, status=400)

            with transaction.atomic():
                compra.proveedor = proveedor
                compra.valor_envio = valor_envio
                compra.save()

                detalles_existentes = {d.producto.id: d for d in compra.detalles.all()}
                nuevos_prod_ids = set()

                for item in productos:
                    prod_id = int(item["id"])
                    cantidad = int(item["cantidad"])
                    costo_unitario = float(item["costo_unitario"])
                    nuevos_prod_ids.add(prod_id)

                    producto = Producto.objects.get(id=prod_id)
                    if costo_unitario > 0:
                        producto.precio_compra = costo_unitario
                        producto.save()

                    if prod_id in detalles_existentes:
                        detalle = detalles_existentes[prod_id]
                        detalle.cantidad = cantidad
                        detalle.costo_unitario = costo_unitario
                        detalle.save()
                    else:
                        DetalleCompra.objects.create(
                            compra=compra,
                            producto=producto,
                            cantidad=cantidad,
                            costo_unitario=costo_unitario
                        )

                for prod_id, detalle in detalles_existentes.items():
                    if prod_id not in nuevos_prod_ids:
                        detalle.delete()

            return JsonResponse({"ok": True, "compra_id": compra.id})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'compras/editar_compra.html', {
        'compra': compra,
        'productos': productos
    })

@login_required
def crear_producto_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse({"ok": False, "error": "No tiene permisos para crear productos."}, status=403)

    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            nombre = datos.get("nombre", "").strip()
            categoria = datos.get("categoria", "General").strip() or "General"
            precio_compra = float(datos.get("precio_compra", 0))
            precio_venta = float(datos.get("precio_venta", 0))
            stock_minimo = int(datos.get("stock_minimo", 5))

            if not nombre:
                return JsonResponse({"ok": False, "error": "El nombre del producto es obligatorio."}, status=400)

            producto = Producto.objects.create(
                nombre=nombre,
                categoria=categoria,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock=0,
                stock_minimo=stock_minimo
            )

            return JsonResponse({
                "ok": True,
                "producto": {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "precio_compra": float(producto.precio_compra),
                    "stock": producto.stock
                }
            })
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
    return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

