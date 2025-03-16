import os
import django
from datetime import datetime, timedelta
import random

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cedepe.settings")
django.setup()

from reservas.models import Hospede, Quarto, Cama, Reserva

def criar_hospedes():
    hospedes_data = [
        {
            "nome": "João Silva",
            "email": "joao@example.com",
            "telefone": "(11) 99999-9999",
            "cpf": "123.456.789-09",
            "endereco": "Rua das Flores, 123 - São Paulo/SP"
        },
        {
            "nome": "Maria Souza",
            "email": "maria@example.com",
            "telefone": "(21) 98888-8888",
            "cpf": "987.654.321-00",
            "endereco": "Avenida Brasil, 456 - Rio de Janeiro/RJ"
        },
        {
            "nome": "Carlos Pereira",
            "email": "carlos@example.com",
            "telefone": "(31) 97777-7777",
            "cpf": "111.222.333-44",
            "endereco": "Rua Central, 789 - Belo Horizonte/MG"
        },
        {
            "nome": "Ana Costa",
            "email": "ana@example.com",
            "telefone": "(41) 96666-6666",
            "cpf": "555.666.777-88",
            "endereco": "Avenida das Nações, 321 - Curitiba/PR"
        },
        {
            "nome": "Pedro Lima",
            "email": "pedro@example.com",
            "telefone": "(51) 95555-5555",
            "cpf": "999.888.777-66",
            "endereco": "Rua dos Andradas, 654 - Porto Alegre/RS"
        }
    ]
    return [Hospede.objects.create(**data) for data in hospedes_data]

def criar_quartos_e_camas():
    for i in range(1, 11):
        quarto = Quarto.objects.create(
            numero=f"{100 + i}",
            descricao=f"Quarto padrão - Andar {random.randint(1, 5)}"
        )
        # Criar 10 camas por quarto
        for j in range(1, 11):
            Cama.objects.create(
                quarto=quarto,
                identificacao=f"Cama {j}",
                status='DISPONIVEL'
            )

def criar_reservas(hospedes):
    # Para cada hóspede, cria uma reserva em uma cama disponível
    for hospede in hospedes:
        # Seleciona aleatoriamente um quarto que possua pelo menos uma cama disponível
        quartos_disponiveis = Quarto.objects.filter(camas__status='DISPONIVEL').distinct()
        if not quartos_disponiveis.exists():
            print("Não há camas disponíveis para reservas.")
            break
        quarto = random.choice(list(quartos_disponiveis))
        # Seleciona a primeira cama disponível do quarto
        cama = quarto.camas.filter(status='DISPONIVEL').first()
        if not cama:
            continue

        checkin = datetime.now() - timedelta(days=random.randint(1, 30))
        checkout = checkin + timedelta(days=random.randint(1, 14))
        status = 'ATIVA' if checkout > datetime.now() else 'FINALIZADA'
        
        # Cria a reserva; o método save() do modelo já atualiza o status da cama
        Reserva.objects.create(
            hospede=hospede,
            cama=cama,
            data_checkin=checkin.date(),
            data_checkout=checkout.date(),
            status=status
        )

        

def main():
    print("Limpando dados existentes...")
    Reserva.objects.all().delete()
    Cama.objects.all().delete()
    Quarto.objects.all().delete()
    Hospede.objects.all().delete()
    
    print("Criando 5 hóspedes...")
    hospedes = criar_hospedes()
    
    print("Criando 10 quartos e 10 camas por quarto...")
    criar_quartos_e_camas()
    
    print("Criando 1 reserva para cada hóspede...")
    criar_reservas(hospedes)
    
    print("\nResumo da população:")
    print(f"- Hóspedes: {Hospede.objects.count()}")
    print(f"- Quartos: {Quarto.objects.count()}")
    print(f"- Camas: {Cama.objects.count()}")
    print(f"- Reservas: {Reserva.objects.count()}")

if __name__ == "__main__":
    main()
