from django.db import models
from django.contrib.auth.models import User

class Setor(models.Model):
    nome = models.CharField(max_length=255)
    
    def __str__(self):
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

class GREUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    escola = models.ForeignKey(Escola, on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    celular = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.user.get_full_name()
    
    def is_gestor(self):
        return self.escola is not None
    
    def is_gre(self):
        return self.setor is not None

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
    
    gestor = models.ForeignKey(GREUser, on_delete=models.CASCADE)
    tipo_problema = models.ForeignKey(TipoProblema, on_delete=models.CASCADE)
    descricao_adicional = models.TextField(blank=True)
    data_relato = models.DateTimeField(auto_now_add=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    foto = models.ImageField(upload_to='relatos_fotos/', blank=True, null=True)
    responsavel = models.ForeignKey(GREUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='problemas_responsavel')
    
    def __str__(self):
        return f"{self.tipo_problema} - {self.gestor.escola.nome if self.gestor.escola else 'Sem escola'}"