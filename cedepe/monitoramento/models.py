from django.db import models
from django.contrib.auth.models import User

class Setor(models.Model):
    nome = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_setores')
    
    def __str__(self):
        return self.nome
    
    @property
    def hierarquia_completa(self):
        if self.parent:
            return f"{self.parent} > {self.nome}"
        return self.nome

class Escola(models.Model):
    nome = models.CharField(max_length=255)
    inep = models.CharField(max_length=20, unique=True)
    email_escola = models.EmailField()
    foto_fachada = models.URLField(blank=True, null=True)
    legenda_foto = models.TextField(blank=True)
    funcao_monitoramento = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.nome

from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User

class GREUser(models.Model):
    # Opções de tipo de usuário corrigidas e organizadas
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador do Sistema'),
        ('COORDENADOR', 'Coordenador GRE'),
        ('CHEFE_SETOR', 'Chefe de Setor'),
        ('MONITOR', 'Monitor Escolar'),
        ('GESTOR', 'Gestor da Escola'),
        ('CEDEPE', 'Técnico CEDEPE/Secretaria'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    escolas = models.ManyToManyField(Escola, blank=True, related_name='usuarios')
    cargo = models.CharField(max_length=100, blank=True)
    tipo_usuario = models.CharField(
        max_length=15,  # Aumentado para caber os novos tipos
        choices=TIPO_USUARIO_CHOICES,
        default='MONITOR',  # Valor padrão ajustado
        verbose_name='Tipo de Usuário'
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF deve estar no formato: 000.000.000-00'
            )
        ],
        verbose_name='CPF'
    )
    celular = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\(\d{2}\) \d{5}-\d{4}$',
                message='Celular deve estar no formato: (99) 99999-9999'
            )
        ]
    )
    
    def __str__(self):
        return self.user.get_full_name()
    
    # Métodos de verificação de perfil atualizados
    def is_gestor(self):
        """Verifica se o usuário é gestor escolar"""
        return self.tipo_usuario == 'GESTOR' and self.escolas.exists()
    
    def is_monitor(self):
        """Verifica se o usuário é monitor escolar"""
        return self.tipo_usuario == 'MONITOR' and self.escolas.exists()
    
    def is_chefe_setor(self):
        """Verifica se o usuário é chefe de setor"""
        return self.tipo_usuario == 'CHEFE_SETOR' and self.setor is not None
    
    def is_coordenador(self):
        """Verifica se o usuário é coordenador da GRE"""
        return self.tipo_usuario == 'COORDENADOR'
    
    def is_cedepes(self):
        """Verifica se o usuário é técnico da CEDEPE/Secretaria"""
        return self.tipo_usuario == 'CEDEPE'
    
    def is_admin(self):
        """Verifica se o usuário é administrador do sistema"""
        return self.tipo_usuario == 'ADMIN'
    
    # Métodos de verificação de acesso atualizados
    def pode_acessar_escola(self, escola):
        """Verifica acesso considerando hierarquia"""
        if self.is_admin() or self.is_coordenador():
            return True
        return escola in self.escolas.all()
    
    def pode_acessar_setor(self, setor):
        """Verifica acesso com hierarquia de setores"""
        if self.is_admin() or self.is_coordenador():
            return True
        if self.is_chefe_setor():
            return setor in self.setor.sub_setores.all() or setor == self.setor
        return self.setor == setor
    
    def setores_permitidos(self):
        """Retorna todos os setores sob responsabilidade"""
        if self.is_admin() or self.is_coordenador():
            return Setor.objects.all()
        if self.is_chefe_setor() and self.setor:
            return Setor.objects.filter(
                models.Q(id=self.setor.id) | 
                models.Q(parent=self.setor)
            )
        return Setor.objects.none()
    
    # Novas propriedades para templates
    @property
    def nivel_acesso(self):
        """Classifica o nível de acesso para exibição"""
        if self.is_admin(): return "Nível Máximo"
        if self.is_coordenador(): return "Nível Estratégico"
        if self.is_chefe_setor(): return "Nível Gerencial"
        return "Nível Operacional"

class Questionario(models.Model):
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateField(auto_now_add=True)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    escolas_destino = models.ManyToManyField(Escola, blank=True)
    
    def __str__(self):
        return self.titulo

class Pergunta(models.Model):
    TIPO_RESPOSTA_CHOICES = [
        ('SN', 'Sim/Não'),
        ('NU', 'Numérico'),
        ('TX', 'Texto'),
    ]
    
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    texto = models.TextField()
    ordem = models.IntegerField()
    tipo_resposta = models.CharField(max_length=2, choices=TIPO_RESPOSTA_CHOICES, default='SN')
    
    def __str__(self):
        return f"{self.ordem} - {self.texto[:50]}"

class Monitoramento(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('R', 'Resolvido'),
        ('U', 'Urgente'),
    ]
    
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    data_envio = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    respondido_por = models.ForeignKey(GREUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.questionario} - {self.escola} - {self.get_status_display()}"
    
    class Meta:
        verbose_name_plural = "Monitoramentos"

class Resposta(models.Model):
    monitoramento = models.ForeignKey(Monitoramento, on_delete=models.CASCADE, related_name='respostas')
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    resposta_sn = models.CharField(max_length=3, choices=[('Sim', 'Sim'), ('Nao', 'Não')], blank=True, null=True)
    resposta_num = models.FloatField(blank=True, null=True)
    resposta_texto = models.TextField(blank=True)
    foto = models.ImageField(upload_to='respostas_fotos/', blank=True, null=True)
    
    def resposta_formatada(self):
        if self.pergunta.tipo_resposta == 'SN':
            return self.resposta_sn
        elif self.pergunta.tipo_resposta == 'NU':
            return str(self.resposta_num)
        return self.resposta_texto
    
    def __str__(self):
        return f"{self.pergunta} - {self.resposta_formatada()}"

class TipoProblema(models.Model):
    descricao = models.CharField(max_length=255)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.descricao

class RelatoProblema(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('R', 'Resolvido'),
        ('U', 'Urgente'),
    ]
    PRIORIDADE_CHOICES = [
        ('A', 'Alta'),
        ('M', 'Média'),
        ('B', 'Baixa'),
    ]
    
    gestor = models.ForeignKey(GREUser, on_delete=models.CASCADE)
    tipo_problema = models.ForeignKey(TipoProblema, on_delete=models.CASCADE)
    descricao_adicional = models.TextField(blank=True)
    data_relato = models.DateTimeField(auto_now_add=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    prioridade = models.CharField(max_length=1, choices=PRIORIDADE_CHOICES, default='M')
    foto = models.ImageField(upload_to='relatos_fotos/', blank=True, null=True)
    responsavel = models.ForeignKey(GREUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='problemas_responsavel')
    solucao_aplicada = models.TextField(blank=True, null=True, verbose_name="Solução Aplicada")
    
    def __str__(self):
        return f"{self.tipo_problema} - {self.gestor.escola.nome if self.gestor.escola else 'Sem escola'}"