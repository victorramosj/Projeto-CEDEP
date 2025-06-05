from django.db import models
from django.utils import timezone

from monitoramento.models import Escola, Setor, GREUser  # ajuste o caminho conforme seu projeto

Pendente = 'P'
Resolvido = 'R'
Em_Andamento = 'E'


# Definir as escolhas de status
STATUS_CHOICES = [
    ('P', 'Pendente'),
    ('R', 'Resolvidos'),
    ('E', 'Em Andamento'),
]

class Lacuna(models.Model):
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='lacunas'
    )
    disciplina = models.CharField(max_length=255)
    carga_horaria = models.PositiveIntegerField(
        help_text="Carga horária em horas-aula"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Lacuna'
        verbose_name_plural = 'Lacunas'

    def __str__(self):
        return f"{self.disciplina} ({self.escola.nome})"
    


class ProblemaUsuario(models.Model):
    usuario = models.ForeignKey(
        GREUser,
        on_delete=models.CASCADE,
        related_name='problemas_reportados'
    )
    setor = models.ForeignKey(
        Setor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='problemas_usuarios'
    )
    descricao = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='problemas',
        default=1
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    anexo = models.FileField(upload_to='problemas/anexos/', null= True, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Problema de Usuário'
        verbose_name_plural = 'Problemas de Usuários'

    def __str__(self):
        setor_nome = self.setor.hierarquia_completa if self.setor else "Geral"
        return f"{self.usuario.user.username} → {setor_nome}"

from django.db import models
from django.utils import timezone

class AvisoImportante(models.Model):
    PRIORIDADES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
    ]
    
    # Mantenha apenas uma definição de setor_destino
    setor_destino = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    
    titulo = models.CharField(max_length=255)
    mensagem = models.TextField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADES, default='normal')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='avisos_problemas')
    criado_por = models.ForeignKey(GREUser, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_exclusao = models.DateTimeField(null=True, blank=True)  # Campo para armazenar a data de exclusão

    def __str__(self):
        return f"[{self.escola.nome}] {self.titulo}"

    def ainda_valido(self):
        return self.ativo and (self.data_expiracao is None or self.data_expiracao >= timezone.now())
