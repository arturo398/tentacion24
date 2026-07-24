from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from ventas.models import Venta, DetalleVenta
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

@login_required
def reportes(request):
    # Verificar que sea Superusuario o Auditor
    user_groups = set(request.user.groups.values_list('name', flat=True))
    es_admin = request.user.is_superuser
    es_auditor = 'Auditor' in user_groups or 'Supervisor' in user_groups or 'Reportes' in user_groups

    if not (es_admin or es_auditor):
        messages.error(request, "No tienes permiso para acceder al módulo de Reportes.")
        return redirect('pos')

    hoy = timezone.now().date()
    ahora = timezone.now()

    ventas_mes = Venta.objects.filter(
        fecha__year=ahora.year,
        fecha__month=ahora.month
    )

    facturacion_mes = sum(venta.total() for venta in ventas_mes)
    ganancia_mes = sum(venta.ganancia() for venta in ventas_mes)
    cantidad_ventas_mes = ventas_mes.count()

    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    facturacion_hoy = sum(venta.total() for venta in ventas_hoy)
    ganancia_hoy = sum(venta.ganancia() for venta in ventas_hoy)
    cantidad_ventas_hoy = ventas_hoy.count()

    top_productos = (
        DetalleVenta.objects
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:10]
    )

    comisiones = []
    for usuario in User.objects.all():
        ventas_usuario = Venta.objects.filter(vendedor=usuario)
        ganancia_total = sum(venta.ganancia() for venta in ventas_usuario)
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

    return render(request, 'reportes/reportes.html', contexto)
