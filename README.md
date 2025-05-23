# Sigref / Cedepe

Este repositório contém o sistema **Sigref** (Sistema de Gestão do GRE Floresta), desenvolvido em Django 5.1, que provê funcionalidades de:

* Gerenciamento de escolas, setores e usuários (GREUser).
* Fluxo de monitoramento e questionários.
* App de problemas e lacunas (em desenvolvimento).

## 📦 Estrutura de Diretórios

* `sigref/` – Projeto Django principal (settings, URLs, WSGI).
* `monitoramento/` – App responsável por questionários, monitoramentos e relatórios.
* `reservas/`, `eventos/` – Outros apps (reservas, eventos).
* **Futuro**: `problemas/` – App standalone para Lacunas e ProblemaUsuario.

## 🚀 Setup Inicial

1. **Clonar o repositório**

   ```bash
   git clone <URL_DO_REPO>
   cd Projeto-CEDEP/sigref
   ```

2. **Criar e ativar ambiente virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate       # Linux/macOS
   venv\Scripts\activate        # Windows
   ```

3. **Instalar dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Variáveis de ambiente**
   Copie e configure o `.env` na raiz do projeto:

   ```ini
   SECRET_KEY=suachavesecreta
   DEBUG=True
   DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DBNAME
   ```

5. **Migrar banco de dados**

   ```bash
   python manage.py migrate
   ```

6. **Criar superusuário**

   ```bash
   python manage.py createsuperuser
   ```

7. **Executar servidor**

   ```bash
   python manage.py runserver
   ```

Acesse `http://localhost:8000/admin` para o painel Django.

## ⚙️ Configurações

Todas as configurações principais estão em `sigref/settings.py`:

* **Banco de dados**: por padrão usa SQLite (`db.sqlite3`).
* **Arquivos estáticos**: configurados para `STATIC_ROOT` e `Whitenoise`.
* **Media**: `MEDIA_ROOT` e `MEDIA_URL`.
* **CORS e CSRF**: `CSRF_TRUSTED_ORIGINS` e cabeçalhos de proxy.
* **REST Framework**: autenticação por sessão e token, paginação.

## 📑 Endpoints Principais

* `/api/escolas/` – CRUD de escolas.
* `/api/setores/` – CRUD de setores.
* `/api/usuarios/` – CRUD de GREUsers.
* `/api/questionarios/` – Questionários.
* `/api/monitoramentos/` – Monitoramentos.
* **Futuro**: `/api/lacunas/` e `/api/problemas-usuario/` no app `problemas`.

## 📂 Scripts de População de Dados

Na pasta `sigref/scripts/`, você encontra scripts para popular o banco de dados com dados de exemplo (sem necessidade de senha):

* **popular.py**: limpa tabelas e importa setores, usuários, escolas, questionários e monitoramentos de exemplo.
* **populate\_db.py**: executa fluxo similar, garantindo a criação de um novo superusuário e populações de Hospedagens.

### Como executar

1. Certifique-se de estar no ambiente virtual e na raiz do projeto (`Projeto-CEDEP/sigref`).
2. Rode o script desejado com Python:

   ```bash
   python sigref/scripts/popular.py
   # ou
   python sigref/scripts/populate_db.py
   ```
3. Cada execução **limpa** os dados existentes (exceto superusuários) e recria tudo do zero.

> ⚠️ Não é necessário configurar senha de banco: os scripts usam a configuração padrão do Django (SQLite) e sempre recriam as tabelas.

## 🛠️ Contribuição

1. Crie uma *branch* para sua feature: `git checkout -b feature/nome-da-feature`
2. Realize as alterações e commite: `git commit -m "Descrição do que foi feito"`
3. Faça *push* para sua branch: `git push origin feature/nome-da-feature`
4. Abra um *Pull Request* descrevendo suas mudanças.

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
