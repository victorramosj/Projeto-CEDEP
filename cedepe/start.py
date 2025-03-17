import os
import webbrowser
from subprocess import Popen

# Caminho para ativação do ambiente virtual
venv_path = os.path.join(os.getcwd(), "venv", "Scripts", "activate.bat")
server_command = "python manage.py runserver"

# Verifica se o ambiente virtual existe antes de ativar
if not os.path.exists(venv_path):
    print("Erro: O ambiente virtual não foi encontrado. Criando um novo...")
    os.system("python -m venv venv")

# Rodar o servidor Django com ativação correta do ambiente virtual
if os.name == "nt":
    Popen(f'start cmd /k "{venv_path} & pip install -r requirements.txt & {server_command}"', shell=True)
else:
    Popen(f"source venv/bin/activate && pip install -r requirements.txt && {server_command}", shell=True)

# Abrir o site automaticamente no navegador
webbrowser.open("http://127.0.0.1:8000/")
