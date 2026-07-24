from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Compra, DetalleCompra
from inventario.models import Producto
from django.http import JsonResponse
from django.db import transaction
import json

@login_required
def listar_compras(request):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a Compras.")
        return redirect('productos')

    compras = Compra.objects.all().order_by('-fecha')
    return render(request, 'compras/listar_compras.html', {'compras': compras})

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
            productos = datos.get("productos", [])

            if not productos:
                return JsonResponse({"ok": False, "error": "Debe agregar al menos un producto"}, status=400)

            with transaction.atomic():
                compra = Compra.objects.create(proveedor=proveedor)
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
