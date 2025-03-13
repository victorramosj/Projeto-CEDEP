# tests.py
'''
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date

from .models import (
    Bem,
    Categoria,
    Departamento,
    Fornecedor,
    Movimentacao,
    LogAlteracao,
)

# Testes para as views que renderizam templates

class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Cria usuário para acessar a view protegida por @login_required
        self.user = User.objects.create_user(username='teste', password='teste123')
        # Cria objetos necessários para o dashboard
        self.categoria = Categoria.objects.create(nome="Categoria1")
        self.departamento = Departamento.objects.create(nome="Departamento1")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor1")
        self.bem1 = Bem.objects.create(
            nome="Bem 1",
            valor=100,
            descricao="Descrição 1",
            status="ativo",
            rfid_tag="RFID1",
            numero_patrimonio="001",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )
        self.bem2 = Bem.objects.create(
            nome="Bem 2",
            valor=200,
            descricao="Descrição 2",
            status="manutencao",
            rfid_tag="RFID2",
            numero_patrimonio="002",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )
        # Cria uma movimentação recente
        self.mov = Movimentacao.objects.create(
            bem=self.bem1,
            origem=self.departamento,
            destino=self.departamento,
            responsavel=self.user
        )

    def test_dashboard_sem_login(self):
        # Deve redirecionar para a página de login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_com_login(self):
        self.client.login(username='teste', password='teste123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Verifica se o contexto contém as variáveis esperadas
        self.assertIn('total_bens', response.context)
        self.assertIn('total_valor', response.context)
        self.assertIn('categorias', response.context)
        self.assertIn('status_counts', response.context)
        self.assertIn('departamentos', response.context)
        self.assertIn('recent_movements', response.context)
        self.assertIn('movimentacoes_hoje', response.context)


class BemFormViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Cria instâncias para popular os selects
        self.categoria = Categoria.objects.create(nome="Categoria Form")
        self.departamento = Departamento.objects.create(nome="Departamento Form")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Form")

    def test_bem_form_view_context(self):
        response = self.client.get(reverse('bem_form'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context)
        self.assertIn('departments', response.context)
        self.assertIn('suppliers', response.context)


class GerenciarBensTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nome="Categoria Busca")
        self.departamento = Departamento.objects.create(nome="Departamento Busca")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Busca")
        self.bem = Bem.objects.create(
            nome="Bem Busca",
            valor=150,
            descricao="Descrição para busca",
            status="ativo",
            rfid_tag="RFIDBUSCA",
            numero_patrimonio="003",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )

    def test_gerenciar_bens_sem_query(self):
        response = self.client.get(reverse('gerenciar_bens'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('bens', response.context)

    def test_gerenciar_bens_com_query(self):
        response = self.client.get(reverse('gerenciar_bens') + '?q=Busca&filter_by=nome')
        self.assertEqual(response.status_code, 200)
        bens = response.context['bens']
        self.assertTrue(bens.object_list.filter(nome__icontains="Busca").exists())


class BuscarTagsRFIDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nome="Categoria RFID")
        self.departamento = Departamento.objects.create(nome="Departamento RFID")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor RFID")
        self.bem = Bem.objects.create(
            nome="Bem RFID",
            valor=100,
            descricao="Teste RFID",
            status="ativo",
            rfid_tag="TAGRFID",
            numero_patrimonio="004",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )

    def test_buscar_tags_rfid_com_query(self):
        response = self.client.get(reverse('buscar_tags_rfid') + '?q=TAG')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tags', data)
        self.assertGreater(len(data['tags']), 0)

    def test_buscar_tags_rfid_sem_query(self):
        response = self.client.get(reverse('buscar_tags_rfid'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['tags'], [])


# Testes para as API views utilizando APIClient

class CriarBemAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='api123')
        self.categoria = Categoria.objects.create(nome="Categoria API")
        self.departamento = Departamento.objects.create(nome="Departamento API")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor API")
        self.client.force_authenticate(user=self.user)

    def test_criar_bem_get_nao_permitido(self):
        response = self.client.get(reverse('criar_bem'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_criar_bem_post_valido(self):
        data = {
            "nome": "Bem API",
            "valor": 300,
            "descricao": "Criado via API",
            "status": "ativo",
            "rfid_tag": "API123",
            "numero_patrimonio": "005",
            "categoria": self.categoria.id,
            "departamento": self.departamento.id,
            "fornecedor": self.fornecedor.id
        }
        response = self.client.post(reverse('criar_bem'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))

    def test_criar_bem_post_invalido(self):
        # Envia dados incompletos (ex.: ausência do campo "nome")
        data = {
            "valor": 300,
            "descricao": "Criado via API",
            "status": "ativo"
        }
        response = self.client.post(reverse('criar_bem'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success'))


class CriarCategoriaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser2', password='api123')
        self.client.force_authenticate(user=self.user)

    def test_criar_categoria_valido(self):
        data = {"nome": "Nova Categoria"}
        response = self.client.post(reverse('criar_categoria'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))

    def test_criar_categoria_invalido(self):
        data = {}  # Campo "nome" ausente
        response = self.client.post(reverse('criar_categoria'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success'))


class CriarDepartamentoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser3', password='api123')
        self.client.force_authenticate(user=self.user)

    def test_criar_departamento_valido(self):
        data = {"nome": "Novo Departamento"}
        response = self.client.post(reverse('criar_departamento'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))

    def test_criar_departamento_invalido(self):
        data = {}
        response = self.client.post(reverse('criar_departamento'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success'))


class CriarFornecedorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser4', password='api123')
        self.client.force_authenticate(user=self.user)

    def test_criar_fornecedor_valido(self):
        data = {"nome": "Novo Fornecedor"}
        response = self.client.post(reverse('criar_fornecedor'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))

    def test_criar_fornecedor_invalido(self):
        data = {}
        response = self.client.post(reverse('criar_fornecedor'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success'))


class EditarBemAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser5', password='api123')
        self.categoria = Categoria.objects.create(nome="Categoria Edit")
        self.departamento = Departamento.objects.create(nome="Departamento Edit")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Edit")
        self.bem = Bem.objects.create(
            nome="Bem Edit",
            valor=400,
            descricao="Antes da edição",
            status="ativo",
            rfid_tag="EDIT123",
            numero_patrimonio="006",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )
        self.client.force_authenticate(user=self.user)

    def test_editar_bem_api_valido(self):
        data = {"descricao": "Depois da edição"}
        url = reverse('editar_bem_api', args=[self.bem.id])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        # Verifica se a descrição foi atualizada
        self.bem.refresh_from_db()
        self.assertEqual(self.bem.descricao, "Depois da edição")

    def test_editar_bem_api_invalido(self):
        data = {"valor": "valor_invalido"}  # Valor numérico esperado
        url = reverse('editar_bem_api', args=[self.bem.id])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success'))

    def test_editar_bem_api_nao_encontrado(self):
        url = reverse('editar_bem_api', args=[9999])
        data = {"descricao": "Teste"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExcluirBemAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser6', password='api123')
        self.categoria = Categoria.objects.create(nome="Categoria Excluir")
        self.departamento = Departamento.objects.create(nome="Departamento Excluir")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Excluir")
        self.bem = Bem.objects.create(
            nome="Bem Excluir",
            valor=500,
            descricao="Para exclusão",
            status="ativo",
            rfid_tag="DEL123",
            numero_patrimonio="007",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )
        self.client.force_authenticate(user=self.user)

    def test_excluir_bem_api(self):
        url = reverse('excluir_bem', args=[self.bem.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Bem.DoesNotExist):
            Bem.objects.get(id=self.bem.id)


# Testes para as views baseadas em formulários (HTML)

class EditarBemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nome="Categoria Edit View")
        self.departamento = Departamento.objects.create(nome="Departamento Edit View")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Edit View")
        self.bem = Bem.objects.create(
            nome="Bem Edit View",
            valor=600,
            descricao="Antes da edição",
            status="ativo",
            rfid_tag="VIEW123",
            numero_patrimonio="008",
            categoria=self.categoria,
            departamento=self.departamento,
            fornecedor=self.fornecedor
        )

    def test_get_editar_bem_view(self):
        url = reverse('editar_bem', args=[self.bem.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('bem', response.context)

    def test_post_editar_bem_view_valido(self):
        url = reverse('editar_bem', args=[self.bem.id])
        data = {
            "nome": "Bem Editado",
            "valor": 600,
            "descricao": "Depois da edição",
            "status": "ativo",
            "rfid_tag": "VIEW123",
            "numero_patrimonio": "008",
            "categoria": self.categoria.id,
            "departamento": self.departamento.id,
            "fornecedor": self.fornecedor.id
        }
        response = self.client.post(url, data)
        # Após edição bem-sucedida, espera-se um redirecionamento
        self.assertEqual(response.status_code, 302)
        self.bem.refresh_from_db()
        self.assertEqual(self.bem.nome, "Bem Editado")


class SimularRFIDViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='rfiduser', password='rfid123')
        self.categoria = Categoria.objects.create(nome="Categoria RFID")
        self.departamento1 = Departamento.objects.create(nome="Depto1")
        self.departamento2 = Departamento.objects.create(nome="Depto2")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor RFID")
        self.bem = Bem.objects.create(
            nome="Bem RFID",
            valor=700,
            descricao="Para simulação",
            status="ativo",
            rfid_tag="RFIDSIM",
            numero_patrimonio="009",
            categoria=self.categoria,
            departamento=self.departamento1,
            fornecedor=self.fornecedor
        )

    def test_simular_rfid_sem_parametro(self):
        url = reverse('simular_rfid')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_simular_rfid_rfid_invalido(self):
        url = reverse('simular_rfid') + '?rfid=INVALID'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_simular_rfid_valido_com_destino(self):
        self.client.login(username='rfiduser', password='rfid123')
        url = reverse('simular_rfid') + f'?rfid=RFIDSIM&destino={self.departamento2.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('mensagem', data)
        # Verifica se o departamento do bem foi atualizado
        self.bem.refresh_from_db()
        self.assertEqual(self.bem.departamento, self.departamento2)

    def test_simular_rfid_valido_sem_destino(self):
        # Caso não seja informado destino, espera-se que a view busque um departamento alternativo
        self.client.login(username='rfiduser', password='rfid123')
        url = reverse('simular_rfid') + '?rfid=RFIDSIM'
        response = self.client.get(url)
        # Se não houver departamento alternativo, retorna 400
        if Departamento.objects.exclude(pk=self.bem.departamento.pk).exists():
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 400)
'''