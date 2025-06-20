import os
import django
from datetime import date

# Configurar ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sigref.settings")
django.setup()

from reservas.models import Quarto, Cama, Ocupacao, Hospede

# Quais camas devem ficar OCUPADAS por quarto
quartos_ocupacoes = {
    '8': [1, 2, 3, 4, 5, 6],  # Todas
    '11': [1, 2, 3, 4, 5, 6],              
    '12': [1, 2, 3, 4, 5, 6],               
}

# Hospede padrão para associar ocupações
def get_or_create_hospede_padrao():
    hospede, _ = Hospede.objects.get_or_create(
        nome="Hóspede Teste",
        defaults={
            'cpf': '000.000.000-00',
            'email': 'teste@teste.com',
            'telefone': '0000-0000',
            'endereco': 'Rua Exemplo',
            'instituicao': 'Não informado'
        }
    )
    return hospede

def resetar_camas_e_ocupacoes():
    hospede = get_or_create_hospede_padrao()

    # Apaga ocupações e camas antigas
    Ocupacao.objects.all().delete()
    Cama.objects.all().delete()

    quartos = Quarto.objects.all()

    for quarto in quartos:
        ocupadas = quartos_ocupacoes.get(quarto.numero, [])
        for i in range(1, 7):  # Criar 6 camas
            cama = Cama.objects.create(
                quarto=quarto,
                identificacao=f"Cama {i}",
                status='DISPONIVEL'
            )
            if i in ocupadas:
                Ocupacao.objects.create(
                    hospede=hospede,
                    cama=cama,
                    data_checkin=date.today(),
                    data_checkout=date.today(),  # ou +7 dias etc.
                    status='ATIVA'
                )
        print(f"✔ Camas recriadas para Quarto {quarto.numero}")

    print(f"🏁 Finalizado. Total camas: {Cama.objects.count()}, Ocupações: {Ocupacao.objects.count()}")

if __name__ == "__main__":
    resetar_camas_e_ocupacoes()
