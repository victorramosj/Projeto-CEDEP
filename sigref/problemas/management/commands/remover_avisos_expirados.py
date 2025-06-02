from django.core.management.base import BaseCommand
from django.utils import timezone
from problemas.models import AvisoImportante  # <-- ESSENCIAL

class Command(BaseCommand):
    help = 'Remove avisos expirados automaticamente.'

    def handle(self, *args, **kwargs):
        agora = timezone.now()
        avisos_expirados = AvisoImportante.objects.filter(ativo=True, data_expiracao__lt=agora)
        count = avisos_expirados.update(ativo=False)
        self.stdout.write(f'{count} avisos expirados foram desativados.')
