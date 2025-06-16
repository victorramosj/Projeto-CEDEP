from django.core.management.base import BaseCommand
from django.utils import timezone
from problemas.models import AvisoImportante

class Command(BaseCommand):
    help = 'Remove avisos expirados automaticamente e os mantém ocultos até a data de expiração.'

    def handle(self, *args, **kwargs):
        agora = timezone.now()

        # Filtrar avisos expirados (data_expiracao menor que agora)
        avisos_expirados = AvisoImportante.objects.filter(ativo=True, data_expiracao__lt=agora)

        if not avisos_expirados:
            self.stdout.write('Nenhum aviso expirado encontrado.')
        else:
            self.stdout.write(f'Data atual: {agora}')
            for aviso in avisos_expirados:
                self.stdout.write(f'Aviso expirado: {aviso.titulo} - Expiração: {aviso.data_expiracao}')
            
            # Atualizar os avisos expirados para inativo (desativar)
            count = avisos_expirados.update(ativo=False)
            self.stdout.write(f'{count} avisos expirados foram desativados.')

            # Agora, excluir fisicamente os avisos expirados (após a data de expiração)
            avisos_para_excluir = AvisoImportante.objects.filter(ativo=False, data_expiracao__lt=agora)
            deletados = avisos_para_excluir.delete()  # Exclui fisicamente
            self.stdout.write(f'{deletados[0]} avisos foram excluídos fisicamente.')
