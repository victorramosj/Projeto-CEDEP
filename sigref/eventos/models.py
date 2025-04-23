from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Sala(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    capacidade = models.PositiveIntegerField()
    localizacao = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.capacidade} pessoas)"

class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    organizador = models.CharField(max_length=100)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Agendamento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='agendamentos')
    salas = models.ManyToManyField(Sala, related_name='agendamentos')
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    participantes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Insira os nomes dos participantes separados por vírgula (opcional)."
    )

    def __str__(self):
        return f"{self.evento.titulo} ({self.inicio} - {self.fim})"
