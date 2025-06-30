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

# seu_app/models.py
class AvisoImportante(models.Model):
    PRIORIDADES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
    ]
    
    setor_destino = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    
    titulo = models.CharField(max_length=255)
    mensagem = models.TextField()
    
    # [MODIFICADO] Campo de imagem agora é opcional
    imagem = models.ImageField(upload_to='avisos_imagens/', null=True, blank=True)
    
    prioridade = models.CharField(max_length=10, choices=PRIORIDADES, default='normal')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='avisos_problemas')
    criado_por = models.ForeignKey(GREUser, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_exclusao = models.DateTimeField(null=True, blank=True)
    visualizado = models.BooleanField(default=False)  # Campo adicionado

    def __str__(self):
        return f"[{self.escola.nome}] {self.titulo}"

    def ainda_valido(self):
        return self.ativo and (self.data_expiracao is None or self.data_expiracao >= timezone.now())

    

# cedepe/models.py

class ConfirmacaoAviso(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('visualizado', 'Visualizado'),
    ]
    
    aviso = models.ForeignKey(AvisoImportante, on_delete=models.CASCADE, related_name='confirmacoes')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='confirmacoes')
    data_recebimento = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS, default='pendente')
    
    def __str__(self):
        return f"Status de {self.escola.nome} para o aviso: {self.aviso.titulo} - {self.status}"
    
    def confirmar_visualizado(self):
        """Método para confirmar que a escola visualizou o aviso"""
        self.status = 'visualizado'
        self.save()  



