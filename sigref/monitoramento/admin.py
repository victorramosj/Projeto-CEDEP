from django.contrib import admin
from django.utils import timezone
from .models import (
    Setor, Escola, GREUser, Questionario, Pergunta,
    Monitoramento, Resposta, TipoProblema, RelatoProblema
)
from django.contrib.admin.filters import EmptyFieldListFilter


# Inlines de Pergunta em Questionário
class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 1
    fields = ('texto', 'ordem', 'tipo_resposta')
    ordering = ('ordem',)


# Inlines de Resposta dentro de um Monitoramento
class RespostaInline(admin.TabularInline):
    model = Resposta
    fk_name = 'monitoramento'
    extra = 0
    fields = (
        'pergunta',
        'resposta_sn',
        'resposta_num',
        'resposta_texto',
        'criado_em',
    )
    readonly_fields = ('pergunta', 'criado_em')

    def has_add_permission(self, request, obj):
        return False


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display    = ('nome', 'hierarquia_completa')
    search_fields   = ('nome',)
    list_filter     = ('parent',)
    ordering        = ('nome',)


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'inep',
        'email_escola',
        'telefone',
        'nome_gestor',
        'telefone_gestor',
        'email_gestor',
        'has_fachada',    # refere-se a este método
        'user_display'
    )
    # … demais configurações …

    def has_fachada(self, obj):
        """
        Retorna True/False para exibir o ícone de check/no ícone
        no admin se a escola tiver foto de fachada.
        """
        return bool(obj.foto_fachada)
    has_fachada.boolean = True
    has_fachada.short_description = 'Tem Fachada'

    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "—"
    user_display.short_description = 'Usuário Vinculado'



@admin.register(GREUser)
class GREUserAdmin(admin.ModelAdmin):
    list_display      = (
        'nome_completo', 'tipo_usuario', 'nivel_acesso',
        'setor', 'escolas_vinculadas', 'cpf', 'celular'
    )
    list_filter       = ('tipo_usuario', 'setor')
    search_fields     = (
        'nome_completo', 'user__username', 'cpf', 'celular'
    )
    filter_horizontal = ('escolas',)
    fieldsets = (
        ('Dados Pessoais', {
            'fields': (
                'user', 'nome_completo', 'cpf', 'celular', 'cargo'
            )
        }),
        ('Vínculos Institucionais', {
            'fields': ('tipo_usuario', 'setor', 'escolas')
        }),
    )

    def escolas_vinculadas(self, obj):
        return ", ".join(e.nome for e in obj.escolas.all())
    escolas_vinculadas.short_description = 'Escolas'


@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display    = (
        'titulo', 'setor', 'criado_por', 'data_criacao',
        'quantidade_perguntas'
    )
    list_filter     = ('setor', 'data_criacao')
    search_fields   = ('titulo', 'descricao')
    inlines         = [PerguntaInline]
    filter_horizontal = ('escolas_destino',)

    def quantidade_perguntas(self, obj):
        return obj.pergunta_set.count()
    quantidade_perguntas.short_description = 'Nº Perguntas'


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display  = ('texto', 'questionario', 'ordem', 'tipo_resposta')
    list_filter   = ('questionario__setor', 'questionario')
    search_fields = ('texto',)
    ordering      = ('questionario', 'ordem')


@admin.register(Monitoramento)
class MonitoramentoAdmin(admin.ModelAdmin):
    list_display    = (
        'escola', 'questionario', 'respondido_por',
        'criado_em', 'atualizado_em', 'foto_comprovante'
    )
    list_filter     = (
        'questionario__setor',
        'escola',
        'respondido_por',
        ('foto_comprovante', EmptyFieldListFilter),
    )
    search_fields   = ('escola__nome', 'questionario__titulo', 'respondido_por__username')
    date_hierarchy  = 'criado_em'
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines         = [RespostaInline]


@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display    = ('monitoramento', 'pergunta', 'resposta_formatada', 'criado_em')
    list_filter     = ('monitoramento__questionario__setor', 'monitoramento__escola')
    search_fields   = ('pergunta__texto',)
    readonly_fields = ('monitoramento', 'pergunta', 'criado_em')

    def resposta_formatada(self, obj):
        return obj.resposta_formatada()
    resposta_formatada.short_description = 'Resposta'


@admin.register(TipoProblema)
class TipoProblemaAdmin(admin.ModelAdmin):
    list_display  = ('descricao', 'setor')
    list_filter   = ('setor',)
    search_fields = ('descricao',)


@admin.register(RelatoProblema)
class RelatoProblemaAdmin(admin.ModelAdmin):
    list_display    = (
        'tipo_problema', 'prioridade', 'status',
        'gestor', 'escola_relacionada', 'data_relato', 'responsavel'
    )
    list_filter     = (
        'tipo_problema__setor', 'status', 'prioridade'
    )
    search_fields   = ('descricao_adicional', 'solucao_aplicada')
    date_hierarchy  = 'data_relato'
    readonly_fields = ('data_relato',)
    actions         = ['marcar_como_resolvido', 'marcar_como_urgente']

    def escola_relacionada(self, obj):
        return obj.gestor.escolas.first().nome if obj.gestor.escolas.exists() else "-"
    escola_relacionada.short_description = 'Escola'

    def marcar_como_resolvido(self, request, queryset):
        queryset.update(status='R', data_resolucao=timezone.now())
    marcar_como_resolvido.short_description = "Marcar como Resolvido"

    def marcar_como_urgente(self, request, queryset):
        queryset.update(status='U')
    marcar_como_urgente.short_description = "Marcar como Urgente"
