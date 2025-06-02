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
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escolas'   # observe o plural
    )  
    
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
        # Exibir nome completo se disponível, caso contrário username
        display_name = self.nome_completo.strip()
        if not display_name:
            display_name = self.user.username
        return f"{display_name} ({self.get_tipo_usuario_display()})"
    
    
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
        """Retorna todos os setores sob responsabilidade considerando a hierarquia completa"""
        from django.db import models
        
        def get_hierarchy(setor):
            """Obtém recursivamente todos os subsetores usando parent"""
            q_objects = models.Q(id=setor.id)  # Inclui o próprio setor
            
            # Primeiro nível de subsetores
            direct_children = models.Q(parent=setor)
            q_objects |= direct_children
            
            # Subsetores dos subsetores (recursivo)
            current_level = Setor.objects.filter(direct_children)
            while current_level.exists():
                next_level = models.Q()
                for child in current_level:
                    next_level |= models.Q(parent=child)
                q_objects |= next_level
                current_level = Setor.objects.filter(next_level)
            
            return Setor.objects.filter(q_objects).distinct()

        if self.is_admin():
            return Setor.objects.all()
        
        if self.is_coordenador() and self.setor:
            # Coordenador vê toda a hierarquia do setor principal
            return get_hierarchy(self.setor)
        
        if self.is_chefe_setor() and self.setor:
            # Chefe vê seu setor e TODOS os subsetores (níveis abaixo)
            return get_hierarchy(self.setor)
        
        return Setor.objects.none()
    
    
    # Adicione este método para facilitar a exibição do tipo de usuário
    def get_tipo_usuario_display(self):
        return dict(self.TIPO_USUARIO_CHOICES).get(self.tipo_usuario, self.tipo_usuario)
    # Novas propriedades para templates
    @property
    def nivel_acesso(self):
        """Classifica o nível de acesso para exibição"""
        if self.is_admin(): return "Nível Máximo"
        if self.is_coordenador(): return "Nível Gerencial"
        if self.is_chefe_setor(): return "Nível Estratégico"
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
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from dateutil.relativedelta import relativedelta

User = get_user_model()

class Monitoramento(models.Model):
    questionario = models.ForeignKey(
        'Questionario', 
        on_delete=models.CASCADE,
        related_name='monitoramentos'
    )
    escola = models.ForeignKey(
        'Escola', 
        on_delete=models.CASCADE,
        related_name='monitoramentos'
    )
    respondido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='monitoramentos'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    foto_comprovante = models.ImageField(
        upload_to='monitoramentos/comprovantes/',
        blank=True,
        null=True,
        verbose_name="Foto Comprobatória"
    )
    @classmethod
    def contagem_hoje(cls, escola, questionario):
        hoje = timezone.now().date()
        return cls.objects.filter(
            escola=escola,
            questionario=questionario,
            criado_em__date=hoje
        ).count()
    
    class Meta:
        verbose_name_plural = "Monitoramentos"
        ordering = ['-criado_em']  # Ordena do mais recente para o mais antigo
        get_latest_by = 'criado_em'

    def __str__(self):
        return f"{self.escola} - {self.questionario} ({self.criado_em:%d/%m/%Y %H:%M})"
    


class Resposta(models.Model):
    monitoramento = models.ForeignKey(
        Monitoramento,
        on_delete=models.CASCADE,
        related_name='respostas'
    )
    pergunta = models.ForeignKey(
        'Pergunta',
        on_delete=models.CASCADE,
        related_name='respostas'
    )
    resposta_sn = models.CharField(
        max_length=3, 
        choices=[('Sim', 'Sim'), ('Nao', 'Não')], 
        blank=True, 
        null=True
    )
    resposta_num = models.FloatField(blank=True, null=True)
    resposta_texto = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def resposta_formatada(self):
        if self.pergunta.tipo_resposta == 'SN':
            return self.resposta_sn
        elif self.pergunta.tipo_resposta == 'NU':
            return str(self.resposta_num)
        return self.resposta_texto

    class Meta:
        unique_together = ('monitoramento', 'pergunta')

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
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)  # Adicione este campo    
    def __str__(self):
        return f"{self.tipo_problema} - {self.escola.nome}"  # Corrigido para usar o campo escola
    