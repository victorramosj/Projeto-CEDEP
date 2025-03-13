# Projeto Gestão de Patrimônio RFID com Django

## Visão Geral
Este projeto tem como objetivo gerenciar inventários utilizando tecnologia RFID, permitindo cadastro, movimentação e monitoramento de bens.

## Tecnologias Utilizadas

- **Linguagem e Frameworks Backend:**
  - Python 3.12
  - Django 5.1.6 – Framework principal para o desenvolvimento da aplicação web.
  - Django REST Framework 3.15.2 – Utilizado para criar os endpoints da API.
  - asgiref 3.8.1 – Biblioteca que fornece a interface ASGI para Django.
  - sqlparse 0.5.3 – Ferramenta para análise e formatação de SQL, usada internamente pelo Django.
  - tzdata 2025.1 – Gerenciamento de fusos horários.

- **Banco de Dados:**
  - SQLite – Banco de dados utilizado para desenvolvimento

- **Frontend e Bibliotecas de Estilo:**
  - Bootstrap 5.3.0 – Framework CSS para responsividade e estilos (via CDN).
  - Bootstrap Icons 1.10.5 – Biblioteca de ícones integrada à interface (via CDN).
  - Chart.js – Biblioteca JavaScript para criação de gráficos (via CDN).

## Estrutura do Projeto
- **core/models.py:** Define os modelos: Bem, Categoria, Departamento, Fornecedor, Movimentacao e LogAlteracao.
- **core/views.py:** Contém as views para renderização do dashboard, formulários e endpoints da API.
- **core/serializers.py:** Serializadores para conversão dos modelos para JSON.
- **/gestao_patrimonio/urls.py:** Integra as URLs do app **core** e as rotas de autenticação e recuperação de senha.
- **core/templates/ e gestao_patrimonio/templates/**: Contém os arquivos HTML do projeto.

## Endpoints da API

### Bens
- **GET /api/bens/**  
  Lista todos os bens cadastrados.

- **POST /api/bens/**  
  Cria um novo bem.

- **GET /api/bens/{id}/**  
  Recupera os detalhes de um bem específico.

- **PUT/PATCH /api/bens/{id}/**  
  Atualiza (total ou parcialmente) os dados de um bem.

- **DELETE /api/bens/{id}/**  
  Exclui um bem.

### Movimentações
- **GET /api/movimentacoes/**  
  Lista todas as movimentações de bens.

- **POST /api/movimentacoes/**  
  Cria uma nova movimentação de bem.

### Ações Específicas
- **POST /api/criar_bem/**  
  Cria um novo bem e registra um log de alteração.  
  *Requer autenticação.*

- **POST /api/criar_categoria/**  
  Cria uma nova categoria.  
  *Requer autenticação.*

- **POST /api/criar_departamento/**  
  Cria um novo departamento.  
  *Requer autenticação.*

- **POST /api/criar_fornecedor/**  
  Cria um novo fornecedor.  
  *Requer autenticação.*

- **PATCH /api/editar_bem/{id}/**  
  Atualiza parcialmente os dados de um bem e registra log de alteração.  
  *Requer autenticação.*

- **DELETE /api/excluir_bem/{id}/**  
  Exclui um bem e registra log de exclusão.  
  *Requer autenticação.*

- **GET /api/buscar_tags_rfid/**  
  Pesquisa por tags RFID. Retorna uma lista de bens cujo campo `rfid_tag` contenha o termo buscado.

- **GET /api/simular_rfid/**  
  Simula a leitura de uma tag RFID e realiza a movimentação do bem para um departamento alternativo, com base nos parâmetros enviados via query string.

## Endpoints do App Gestão de Patrimônio

### Dashboard e Página Principal
- **GET /**  
  Exibe o dashboard principal com informações gerais sobre os bens cadastrados.

### Autenticação e Cadastro de Usuários
- **GET/POST /login/**  
  Exibe o formulário de login e autentica o usuário.

- **GET /logout/**  
  Realiza o logout do usuário e redireciona para a página principal.

- **GET/POST /register/**  
  Exibe o formulário de registro e cria uma nova conta de usuário.

### Recuperação de Senha
- **GET/POST /password_reset/**  
  Exibe o formulário para solicitar a recuperação de senha e envia um e-mail com instruções.

- **GET /password_reset_done/**  
  Exibe uma mensagem informando que as instruções para recuperação de senha foram enviadas.

- **GET/POST /password_reset_confirm/<uidb64>/<token>/**  
  Exibe o formulário para redefinir a senha utilizando o link enviado por e-mail.

- **GET /password_reset_complete/**  
  Confirma que a senha foi redefinida com sucesso e exibe uma mensagem de confirmação.
