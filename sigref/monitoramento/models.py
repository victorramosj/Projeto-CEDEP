from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from dateutil.relativedelta import relativedelta

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
    nome_gestor = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='escola')
    endereco = models.TextField(
        verbose_name="Endereço da Escola",
        blank=True,
        help_text="Ex: Rua ABC, 123 - Bairro XYZ"
    )
    foto_fachada = models.ImageField(
        upload_to='escolas/fachadas/',
        blank=True,
        null=True,
        verbose_name="Foto da Fachada"
    )    
    email_gestor = models.EmailField(
        verbose_name="Email do Gestor",
        blank=True,
        help_text="Email oficial do gestor responsável"
    )
    telefone = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\(\d{2}\) \d{5}-\d{4}$',
                message='Celular deve estar no formato: (99) 99999-9999'
            )
        ]
    )
    telefone_gestor = models.CharField(
        max_length=15,
        blank=True,        
    )
        
    def __str__(self):
        return self.nome


from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class GREUser(models.Model):
    # Opções de tipo de usuário corrigidas e organizadas
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador do Sistema'),
        ('COORDENADOR', 'Coordenador GRE'),
        ('CHEFE_SETOR', 'Chefe de Setor'),
        ('MONITOR', 'Monitor Escolar'),
        ('ESCOLA', 'Escola'), 
        ('CEDEPE', 'Técnico CEDEPE/Secretaria'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    escolas = models.ManyToManyField(Escola, blank=True, related_name='usuarios')
    cargo = models.CharField(max_length=100, blank=True)
    nome_completo = models.CharField(max_length=255, blank=True)
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
    def is_escola(self):
        """Verifica se o usuário é a escola"""
        return self.tipo_usuario == 'ESCOLA' and self.escolas.exists()
    
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
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Adicione esta linha
    
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
    FREQUENCIA_CHOICES = [
        ('D', 'Diário'),
        ('S', 'Semanal'),
        ('Q', 'Quinzenal'),
        ('M', 'Mensal'),
        ('6', 'Semestral'),
        ('A', 'Anual'),
    ]
    
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    data_envio = models.DateTimeField(auto_now_add=True)
    data_limite = models.DateField(default=timezone.now)  # Adicione default
    frequencia = models.CharField(
        max_length=1, 
        choices=FREQUENCIA_CHOICES, 
        default='S',
        verbose_name="Periodicidade"
    )
    data_resposta = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    respondido_por = models.ForeignKey(GREUser, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)  # Novo campo para controle
    atualizado_em = models.DateTimeField(auto_now=True)  # Novo campo para controle
    
    class Meta:
        verbose_name_plural = "Monitoramentos"
        ordering = ['data_limite']
    
    @classmethod
    def calcular_proxima_data(cls, frequencia, data_base=None):
        if data_base is None:
            data_base = timezone.now().date()
            
        if frequencia == 'D':
            return data_base + relativedelta(days=1)
        elif frequencia == 'S':
            return data_base + relativedelta(weeks=1)
        elif frequencia == 'Q':
            return data_base + relativedelta(weeks=2)
        elif frequencia == 'M':
            return data_base + relativedelta(months=1)
        elif frequencia == '6':
            return data_base + relativedelta(months=6)
        elif frequencia == 'A':
            return data_base + relativedelta(years=1)
        return data_base
    
    def save(self, *args, **kwargs):
        if not self.data_limite:  # Só calcula se não tiver data definida
            self.data_limite = self.calcular_proxima_data(self.frequencia)
        super().save(*args, **kwargs)

        
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