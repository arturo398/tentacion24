def roles_usuario(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'es_admin': False,
            'es_auditor': False,
            'es_vendedor': False,
        }

    es_admin = request.user.is_superuser
    user_groups = set(request.user.groups.values_list('name', flat=True))
    
    es_auditor = 'Auditor' in user_groups or 'Supervisor' in user_groups or 'Reportes' in user_groups
    es_vendedor = 'Vendedor' in user_groups or 'Cajero' in user_groups

    return {
        'es_admin': es_admin,
        'es_auditor': es_auditor,
        'es_vendedor': es_vendedor,
    }
