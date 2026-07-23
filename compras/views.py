from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Compra, DetalleCompra
from inventario.models import Producto
from django.http import JsonResponse
from django.db import transaction
import json

@login_required
def listar_compras(request):
    compras = Compra.objects.all().order_by('-fecha')
    return render(request, 'compras/listar_compras.html', {'compras': compras})

@login_required
def registrar_compra(request):
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
                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        costo_unitario=costo_unitario
                    )
            return JsonResponse({"ok": True, "compra_id": compra.id})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    productos = Producto.objects.all()
    return render(request, 'compras/registrar_compra.html', {'productos': productos})
