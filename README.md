# Sistema de Controle de Hospedagens e Eventos - CEDEPE

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

Sistema completo para gestão de hospedagens e eventos desenvolvido com Django. Integrado com PostgreSQL e deploy automatizado no Railway.

## 🛠️ Funcionalidades Principais

### 🏨 Módulo de Hospedagem
- Cadastro de quartos com múltiplas camas
- Controle de status de ocupação em tempo real
- Gestão de hóspedes com dados completos
- Sistema de reservas com confirmação automática
- Histórico completo de ocupações

### 📅 Módulo de Eventos
- Cadastro de salas com capacidade específica
- Agendamento de eventos com múltiplas salas
- Controle de participantes e organizadores
- Sistema de conflitos de horários
- Integração com calendários

## ⚙️ Tecnologias Utilizadas
- Django 5.1.7
- PostgreSQL
- Django REST Framework
- WhiteNoise (Gestão de arquivos estáticos)
- Railway (Deploy e hosting)

## 🚀 Primeiros Passos

### Pré-requisitos
- Python 3.10+
- PostgreSQL
- Pipenv (opcional)

### Instalação Local
```bash
git clone https://github.com/seu-usuario/Projeto-CEDEP.git
cd cedepe

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar o .env com suas credenciais

# Migrações e superusuário
python manage.py migrate
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
