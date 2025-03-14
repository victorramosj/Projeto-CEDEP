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
    quartos = Quarto.objects.all()
    for quarto in quartos:
        camas = quarto.camas.all()[:2]  # Reservar 2 camas por quarto
        
        for i, cama in enumerate(camas):
            hospede = random.choice(hospedes)
            checkin = datetime.now() - timedelta(days=random.randint(1, 30))
            checkout = checkin + timedelta(days=random.randint(1, 14))
            
            Reserva.objects.create(
                hospede=hospede,
                cama=cama,
                data_checkin=checkin.date(),
                data_checkout=checkout.date(),
                status='ATIVA' if checkout > datetime.now() else 'FINALIZADA'
            )
            cama.status = 'OCUPADA'
            cama.save()

def main():
    print("Limpando dados existentes...")
    Reserva.objects.all().delete()
    Cama.objects.all().delete()
    Quarto.objects.all().delete()
    Hospede.objects.all().delete()
    
    print("Criando hóspedes...")
    hospedes = criar_hospedes()
    
    print("Criando quartos e camas...")
    criar_quartos_e_camas()
    
    print("Criando reservas...")
    criar_reservas(hospedes)
    
    print("\nResumo da população:")
    print(f"- Hóspedes: {Hospede.objects.count()}")
    print(f"- Quartos: {Quarto.objects.count()}")
    print(f"- Camas: {Cama.objects.count()}")
    print(f"- Reservas: {Reserva.objects.count()}")

if __name__ == "__main__":
    main()