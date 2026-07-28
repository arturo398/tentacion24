import io
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from ventas.models import Venta, DetalleVenta
from compras.models import Compra
from inventario.models import ConfiguracionCaja
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


MESES_NOMBRES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


@login_required
def reportes(request):
    # Verificar que sea Superusuario o Auditor
    user_groups = set(request.user.groups.values_list('name', flat=True))
    es_admin = request.user.is_superuser
    es_auditor = 'Auditor' in user_groups or 'Supervisor' in user_groups or 'Reportes' in user_groups

    if not (es_admin or es_auditor):
        messages.error(request, "No tienes permiso para acceder al módulo de Reportes.")
        return redirect('pos')

    hoy = timezone.localdate()
    ahora = timezone.localtime()

    # Capturar mes y año seleccionados (GET)
    try:
        mes_sel = int(request.GET.get('mes', ahora.month))
    except (ValueError, TypeError):
        mes_sel = ahora.month

    try:
        anio_sel = int(request.GET.get('anio', ahora.year))
    except (ValueError, TypeError):
        anio_sel = ahora.year

    if mes_sel not in MESES_NOMBRES:
        mes_sel = ahora.month

    # Cálculo de Semana de Lunes a Lunes (Lunes 00:00:00 a Próximo Lunes 00:00:00)
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    domingo_actual = lunes_actual + timedelta(days=6)
    proximo_lunes = lunes_actual + timedelta(days=7)

    # Métricas Hoy
    ventas_hoy = Venta.objects.filter(fecha__date=hoy).prefetch_related('detalles__producto')
    facturacion_hoy = sum((venta.total() for venta in ventas_hoy), Decimal('0.00'))
    ganancia_hoy = sum((venta.ganancia() for venta in ventas_hoy), Decimal('0.00'))
    cantidad_ventas_hoy = ventas_hoy.count()

    # Métricas Semanal (Lunes a Lunes)
    ventas_semana = Venta.objects.filter(fecha__date__gte=lunes_actual, fecha__date__lt=proximo_lunes).prefetch_related('detalles__producto')
    facturacion_semana = sum((venta.total() for venta in ventas_semana), Decimal('0.00'))
    ganancia_semana = sum((venta.ganancia() for venta in ventas_semana), Decimal('0.00'))
    cantidad_ventas_semana = ventas_semana.count()

    # Métricas Mes Seleccionado
    ventas_mes = Venta.objects.filter(
        fecha__year=anio_sel,
        fecha__month=mes_sel
    ).prefetch_related('detalles__producto')
    facturacion_mes = sum((venta.total() for venta in ventas_mes), Decimal('0.00'))
    ganancia_mes = sum((venta.ganancia() for venta in ventas_mes), Decimal('0.00'))
    cantidad_ventas_mes = ventas_mes.count()

    nombre_mes_sel = MESES_NOMBRES.get(mes_sel, '')

    top_productos = (
        DetalleVenta.objects
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:10]
    )

    comisiones = []
    todas_ventas = Venta.objects.prefetch_related('detalles__producto')
    for usuario in User.objects.all():
        ventas_usuario = [v for v in todas_ventas if v.vendedor_id == usuario.id]
        ganancia_total = sum((venta.ganancia() for venta in ventas_usuario), Decimal('0.00'))
        comision = ganancia_total * Decimal('0.20')

        comisiones.append({
            'usuario': usuario.username,
            'ganancia': ganancia_total,
            'comision': comision
        })

    rango_semana = f"Lunes {lunes_actual.strftime('%d/%m')} al Domingo {domingo_actual.strftime('%d/%m')}"

    caja_config = ConfiguracionCaja.obtener_configuracion()
    caja_inicial = caja_config.monto_inicial
    fecha_inicio_caja = caja_config.fecha_inicio_caja

    ventas_caja = Venta.objects.filter(fecha__date__gte=fecha_inicio_caja)
    compras_caja = Compra.objects.filter(fecha__date__gte=fecha_inicio_caja)
    compras_inversion = Compra.objects.filter(fecha__date__lt=fecha_inicio_caja)

    facturacion_caja = sum((v.total() for v in ventas_caja), Decimal('0.00'))
    compras_caja_monetario = sum((c.total() for c in compras_caja), Decimal('0.00'))
    inversion_inicial = sum((c.total() for c in compras_inversion), Decimal('0.00'))

    saldo_caja = Decimal(str(caja_inicial)) + facturacion_caja - compras_caja_monetario

    meses_opciones = [{'numero': k, 'nombre': v} for k, v in MESES_NOMBRES.items()]
    anios_opciones = list(range(2025, ahora.year + 2))

    contexto = {
        'facturacion_hoy': facturacion_hoy,
        'ganancia_hoy': ganancia_hoy,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'facturacion_semana': facturacion_semana,
        'ganancia_semana': ganancia_semana,
        'cantidad_ventas_semana': cantidad_ventas_semana,
        'rango_semana': rango_semana,
        'facturacion_mes': facturacion_mes,
        'ganancia_mes': ganancia_mes,
        'cantidad_ventas_mes': cantidad_ventas_mes,
        'top_productos': top_productos,
        'comisiones': comisiones,
        'caja_inicial': caja_inicial,
        'fecha_inicio_caja': fecha_inicio_caja,
        'facturacion_caja': facturacion_caja,
        'compras_caja_monetario': compras_caja_monetario,
        'inversion_inicial': inversion_inicial,
        'saldo_caja': saldo_caja,
        'mes_sel': mes_sel,
        'anio_sel': anio_sel,
        'nombre_mes_sel': nombre_mes_sel,
        'meses_opciones': meses_opciones,
        'anios_opciones': anios_opciones,
    }

    return render(request, 'reportes/reportes.html', contexto)


@login_required
def generar_pdf_reporte(request):
    user_groups = set(request.user.groups.values_list('name', flat=True))
    es_admin = request.user.is_superuser
    es_auditor = 'Auditor' in user_groups or 'Supervisor' in user_groups or 'Reportes' in user_groups

    if not (es_admin or es_auditor):
        messages.error(request, "No tienes permiso para descargar reportes.")
        return redirect('pos')

    tipo = request.GET.get('tipo', 'semanal').lower()
    ahora = timezone.localtime()
    hoy = timezone.localdate()

    lunes_actual = hoy - timedelta(days=hoy.weekday())
    domingo_actual = lunes_actual + timedelta(days=6)
    proximo_lunes = lunes_actual + timedelta(days=7)

    if tipo == 'semanal':
        ventas_periodo = Venta.objects.filter(fecha__date__gte=lunes_actual, fecha__date__lt=proximo_lunes)
        detalles_periodo = DetalleVenta.objects.filter(venta__in=ventas_periodo)
        titulo_pdf = f"TENTACIÓN 24 - Reporte Semanal (Lunes {lunes_actual.strftime('%d/%m')} a Domingo {domingo_actual.strftime('%d/%m')})"
        nombre_archivo = f"reporte_semanal_tentacion24_{lunes_actual.strftime('%Y%m%d')}.pdf"
        subtitulo_periodo = f"Período Semanal: Lunes {lunes_actual.strftime('%d/%m/%Y')} al Domingo {domingo_actual.strftime('%d/%m/%Y')}"
    else: # mensual
        try:
            mes_sel = int(request.GET.get('mes', ahora.month))
        except (ValueError, TypeError):
            mes_sel = ahora.month

        try:
            anio_sel = int(request.GET.get('anio', ahora.year))
        except (ValueError, TypeError):
            anio_sel = ahora.year

        nombre_mes = MESES_NOMBRES.get(mes_sel, str(mes_sel))
        ventas_periodo = Venta.objects.filter(fecha__year=anio_sel, fecha__month=mes_sel)
        detalles_periodo = DetalleVenta.objects.filter(venta__in=ventas_periodo)
        titulo_pdf = f"TENTACIÓN 24 - Reporte Mensual ({nombre_mes} {anio_sel})"
        nombre_archivo = f"reporte_mensual_{nombre_mes.lower()}_{anio_sel}.pdf"
        subtitulo_periodo = f"Período Mensual: {nombre_mes} {anio_sel}"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'ReportSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )

    elements.append(Paragraph(titulo_pdf, title_style))
    elements.append(Paragraph(f"{subtitulo_periodo} | Emisión: {ahora.strftime('%d/%m/%Y %H:%M')} | Por: {request.user.username}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Métricas del Período Seleccionado
    facturacion_periodo = sum((v.total() for v in ventas_periodo), Decimal('0.00'))
    ganancia_periodo = sum((v.ganancia() for v in ventas_periodo), Decimal('0.00'))
    cantidad_ventas = ventas_periodo.count()

    summary_data = [
        ['Métrica', 'Valor'],
        ['Cantidad de Ventas', str(cantidad_ventas)],
        ['Facturación Total (Ventas + Envío Moto)', f"${facturacion_periodo:.2f}"],
        ['Ganancia Neta (Ventas Productos - Costos)', f"${ganancia_periodo:.2f}"]
    ]

    table_summary = Table(summary_data, colWidths=[270, 270])
    table_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    elements.append(Paragraph("<b>Resumen Financiero del Período</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    elements.append(table_summary)
    elements.append(Spacer(1, 20))

    # Top productos del período
    top_productos_periodo = (
        detalles_periodo
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:10]
    )

    prod_data = [['#', 'Producto', 'Unidades Vendidas']]
    for idx, p in enumerate(top_productos_periodo, start=1):
        prod_data.append([str(idx), p['producto__nombre'], str(p['total_vendido'])])

    if len(prod_data) == 1:
        prod_data.append(['-', 'No hay ventas registradas en el período', '0'])

    table_prod = Table(prod_data, colWidths=[40, 340, 160])
    table_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284C7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    elements.append(Paragraph("<b>Productos Más Vendidos en el Período</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    elements.append(table_prod)
    elements.append(Spacer(1, 20))

    # Comisiones del período
    com_data = [['Vendedor', 'Ganancia Generada en Período', 'Comisión (20%)']]
    for usuario in User.objects.all():
        ventas_u = ventas_periodo.filter(vendedor=usuario)
        ganancia_u = sum((v.ganancia() for v in ventas_u), Decimal('0.00'))
        if ganancia_u > 0 or usuario.is_superuser:
            comision = ganancia_u * Decimal('0.20')
            com_data.append([usuario.username, f"${ganancia_u:.2f}", f"${comision:.2f}"])

    if len(com_data) == 1:
        com_data.append(['Sin comisiones en el período', '$0.00', '$0.00'])

    table_com = Table(com_data, colWidths=[200, 170, 170])
    table_com.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#16A34A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    elements.append(Paragraph("<b>Comisiones de Vendedores del Período</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    elements.append(table_com)

    doc.build(elements)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response

