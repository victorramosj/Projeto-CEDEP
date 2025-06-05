from django.core.management.base import BaseCommand
from django.utils import timezone
from problemas.models import AvisoImportante

class Command(BaseCommand):
    help = 'Remove avisos expirados automaticamente e os mantém ocultos até o período de exclusão.'

    def handle(self, *args, **kwargs):
        agora = timezone.now()
        avisos_expirados = AvisoImportante.objects.filter(ativo=True, data_expiracao__lt=agora)

        # Verificação do log
        self.stdout.write(f'Data atual: {agora}')
        for aviso in avisos_expirados:
            self.stdout.write(f'Aviso expirado: {aviso.titulo} - Expiração: {aviso.data_expiracao}')
        
        # Marcar para exclusão após 7 dias (você pode alterar esse período)
        dias_ate_exclusao = 7
        data_exclusao = agora + timezone.timedelta(days=dias_ate_exclusao)

        # Atualiza os registros para indicar que estão aguardando exclusão
        count = avisos_expirados.update(ativo=False, data_exclusao=data_exclusao)
        self.stdout.write(f'{count} avisos expirados foram desativados e aguardam exclusão até {data_exclusao}.')
