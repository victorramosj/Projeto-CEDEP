from django.db import models
from django.utils import timezone

from monitoramento.models import Escola, Setor, GREUser  # ajuste o caminho conforme seu projeto

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

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Problema de Usuário'
        verbose_name_plural = 'Problemas de Usuários'

    def __str__(self):
        setor_nome = self.setor.hierarquia_completa if self.setor else "Geral"
        return f"{self.usuario.user.username} → {setor_nome}"

