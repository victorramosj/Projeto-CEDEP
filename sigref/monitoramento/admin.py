from django.contrib import admin
from django.utils import timezone
from .models import (
    Setor, Escola, GREUser, Questionario, Pergunta, 
    Monitoramento, Resposta, TipoProblema, RelatoProblema
)
from django.contrib.admin.filters import EmptyFieldListFilter
class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 1
    fields = ('texto', 'ordem', 'tipo_resposta')
    ordering = ('ordem',)

class RespostaInline(admin.TabularInline):
    model = Resposta
    fk_name = 'monitoramento'  # <-- esta linha é essencial
    extra = 0
    fields = ('pergunta', 'resposta_sn', 'resposta_num', 'resposta_texto', 'foto')
    readonly_fields = ('pergunta',)

    def has_add_permission(self, request, obj):
        return False



@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'hierarquia_completa')
    search_fields = ('nome',)
    list_filter = ('parent',)

    def hierarquia_completa(self, obj):
        return obj.hierarquia_completa
    hierarquia_completa.short_description = 'Hierarquia'

from django.contrib import admin
from django.contrib.auth.models import User
from django import forms
from .models import Escola

class EscolaForm(forms.ModelForm):
    class Meta:
        model = Escola
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user' in self.fields:
            self.fields['user'].queryset = User.objects.order_by('first_name', 'last_name')
            self.fields['user'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    form = EscolaForm
    list_display = (
        'nome',
        'inep',
        'email_escola',
        'telefone',
        'nome_gestor',
        'telefone_gestor',
        'email_gestor',
        'has_fachada',
        'user_display'
    )
    
    search_fields = (
        'nome',
        'inep',
        'email_escola',
        'telefone',
        'nome_gestor',
        'telefone_gestor',
        'email_gestor',
        'user__username',
        'user__first_name',
        'user__last_name'
    )
    
    list_filter = (
        ('user', admin.EmptyFieldListFilter),
        ('foto_fachada', admin.EmptyFieldListFilter),
    )
    
    ordering = ('nome',)
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('nome', 'inep', 'email_escola', 'endereco', 'user')
        }),
        ('Contato da Escola', {
            'fields': ('telefone', 'foto_fachada'),
        }),
        ('Gestor', {
            'fields': ('nome_gestor', 'telefone_gestor', 'email_gestor'),
        }),
    )

    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "Nenhum usuário vinculado"
    user_display.short_description = 'Usuário Vinculado'

    def has_fachada(self, obj):
        return bool(obj.foto_fachada)
    has_fachada.boolean = True
    has_fachada.short_description = 'Tem foto de fachada'
    
@admin.register(GREUser)
class GREUserAdmin(admin.ModelAdmin):
    list_display = (
        'nome_completo',  # Campo personalizado
        'tipo_usuario', 
        'nivel_acesso', 
        'setor', 
        'escolas_vinculadas', 
        'cpf', 
        'celular'
    )
    list_filter = ('tipo_usuario', 'setor')
    search_fields = (
        'nome_completo',  # Busca por nome completo
        'user__username', 
        'cpf', 
        'celular'
    )
    filter_horizontal = ('escolas',)
    fieldsets = (
        ('Dados Pessoais', {
            'fields': (
                'user', 
                'nome_completo',  # Campo adicionado
                'cpf', 
                'celular', 
                'cargo'
            )
        }),
        ('Vinculos Institucionais', {
            'fields': ('tipo_usuario', 'setor', 'escolas')
        }),
    )

    def nivel_acesso(self, obj):
        return obj.nivel_acesso
    nivel_acesso.short_description = 'Nível de Acesso'

    def escolas_vinculadas(self, obj):
        return ", ".join([e.nome for e in obj.escolas.all()])
    escolas_vinculadas.short_description = 'Escolas'

@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'setor', 'data_criacao', 'quantidade_perguntas')
    list_filter = ('setor', 'data_criacao')
    search_fields = ('titulo', 'descricao')
    inlines = [PerguntaInline]
    filter_horizontal = ('escolas_destino',)

    def quantidade_perguntas(self, obj):
        return obj.pergunta_set.count()
    quantidade_perguntas.short_description = 'Perguntas'

@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'questionario', 'ordem', 'tipo_resposta')
    list_filter = ('questionario__setor', 'questionario')
    search_fields = ('texto',)
    ordering = ('questionario', 'ordem')

@admin.register(Monitoramento)
class MonitoramentoAdmin(admin.ModelAdmin):
    list_display = ('questionario', 'escola', 'status', 'data_envio', 'respondido_por')
    list_filter = ('questionario__setor', 'status', 'escola')
    search_fields = ('escola__nome', 'questionario__titulo')
    date_hierarchy = 'data_envio'
    inlines = [RespostaInline]
    readonly_fields = ('data_envio', 'data_resposta')
    actions = ['marcar_como_resolvido', 'marcar_como_urgente']

    def marcar_como_resolvido(self, request, queryset):
        queryset.update(status='R', data_resposta=timezone.now())
    marcar_como_resolvido.short_description = "Marcar como Resolvido"

    def marcar_como_urgente(self, request, queryset):
        queryset.update(status='U')
    marcar_como_urgente.short_description = "Marcar como Urgente"

@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display = ('monitoramento', 'pergunta', 'resposta_formatada')
    list_filter = ('monitoramento__questionario__setor', 'monitoramento__escola')
    search_fields = ('pergunta__texto',)
    readonly_fields = ('monitoramento', 'pergunta')

    def resposta_formatada(self, obj):
        return obj.resposta_formatada()
    resposta_formatada.short_description = 'Resposta'

@admin.register(TipoProblema)
class TipoProblemaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'setor')
    list_filter = ('setor',)
    search_fields = ('descricao',)

@admin.register(RelatoProblema)
class RelatoProblemaAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_problema', 'prioridade', 'status', 
        'gestor', 'escola_relacionada', 'data_relato', 'responsavel'
    )
    list_filter = ('tipo_problema__setor', 'status', 'prioridade')
    search_fields = ('descricao_adicional', 'solucao_aplicada')
    date_hierarchy = 'data_relato'
    readonly_fields = ('data_relato',)
    actions = ['marcar_como_resolvido', 'marcar_como_urgente']

    def escola_relacionada(self, obj):
        return obj.gestor.escolas.first().nome if obj.gestor.escolas.exists() else '-'
    escola_relacionada.short_description = 'Escola'

    def marcar_como_resolvido(self, request, queryset):
        queryset.update(status='R', data_resolucao=timezone.now())
    marcar_como_resolvido.short_description = "Marcar como Resolvido"

    def marcar_como_urgente(self, request, queryset):
        queryset.update(status='U')
    marcar_como_urgente.short_description = "Marcar como Urgente"