from django.apps import AppConfig
from django.db.models.signals import post_migrate

def crear_grupos_iniciales(sender, **kwargs):
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='Auditor')
    Group.objects.get_or_create(name='Vendedor')

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'

    def ready(self):
        post_migrate.connect(crear_grupos_iniciales, sender=self)
