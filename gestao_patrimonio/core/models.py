from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=150)
    cnpj_cpf = models.CharField(max_length=18, unique=True, default="00000000000000")
    contato = models.CharField(max_length=100)
    endereco = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nome} - {self.cnpj_cpf}"

class Departamento(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Bem(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('descartado', 'Descartado')
    ]

    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    data_aquisicao = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    numero_patrimonio = models.CharField(max_length=50, unique=True)  # Número de tombamento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    rfid_tag = models.CharField(max_length=12, unique=True, blank=True, null=True)
    def __str__(self):
        return f"{self.nome} - {self.numero_patrimonio}"

class Movimentacao(models.Model):
    bem = models.ForeignKey(Bem, on_delete=models.SET_NULL, null=True)
    origem = models.ForeignKey(Departamento, related_name="movimentacoes_origem", on_delete=models.CASCADE)
    destino = models.ForeignKey(Departamento, related_name="movimentacoes_destino", on_delete=models.CASCADE)
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Usuário que fez a movimentação

    def __str__(self):
        if self.bem:
            return f"{self.bem.nome} de {self.origem} para {self.destino} ({self.data_movimentacao.strftime('%d/%m/%Y %H:%M')})"
        else:
            return f"Movimentação: Bem excluído de {self.origem} para {self.destino} ({self.data_movimentacao.strftime('%d/%m/%Y %H:%M')})"

class LogAlteracao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    bem = models.ForeignKey(Bem, on_delete=models.SET_NULL, null=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField()  # Exemplo: "Status alterado de Ativo para Manutenção"

    def __str__(self):
        if self.bem:
            return f"{self.bem.nome} - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"
        else:
            return f"Bem excluído - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"
