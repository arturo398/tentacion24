from urllib import request
from django.contrib.auth.models import User
from django.shortcuts import render
from ventas.models import Venta
from django.utils import timezone
from django.db.models import Sum
from ventas.models import DetalleVenta
from decimal import Decimal
# Create your views here.

def reportes(request):

    hoy = timezone.now().date()

    ahora = timezone.now()

    ventas_mes = Venta.objects.filter(
        fecha__year=ahora.year,
        fecha__month=ahora.month
    )

    facturacion_mes = sum(
        venta.total()
        for venta in ventas_mes
    )

    ganancia_mes = sum(
        venta.ganancia()
        for venta in ventas_mes
    )

    cantidad_ventas_mes = ventas_mes.count()

    ventas_hoy = Venta.objects.filter(
        fecha__date=hoy
    )

    facturacion_hoy = sum(
        venta.total()
        for venta in ventas_hoy
    )

    ganancia_hoy = sum(
        venta.ganancia()
        for venta in ventas_hoy
    )

    cantidad_ventas_hoy = ventas_hoy.count()

    top_productos = (
    DetalleVenta.objects
    .values('producto__nombre')
    .annotate(total_vendido=Sum('cantidad'))
    .order_by('-total_vendido')[:10]
    )

    comisiones = []

    for usuario in User.objects.all():

        ventas_usuario = Venta.objects.filter(
            vendedor=usuario
        )

        ganancia_total = sum(
            venta.ganancia()
            for venta in ventas_usuario
        )

        comision = ganancia_total * Decimal('0.20')

        comisiones.append({
            'usuario': usuario.username,
            'ganancia': ganancia_total,
            'comision': comision
        })
    
    contexto = {
        'facturacion_hoy': facturacion_hoy,
        'ganancia_hoy': ganancia_hoy,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'facturacion_mes': facturacion_mes,
        'ganancia_mes': ganancia_mes,
        'cantidad_ventas_mes': cantidad_ventas_mes,
        'top_productos': top_productos,
        'comisiones': comisiones
    }



    return render(
        request,
        'reportes/reportes.html',
        contexto
    )
