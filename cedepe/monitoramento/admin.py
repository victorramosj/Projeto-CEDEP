from django.contrib import admin
from .models import (
    Setor, Escola, GREUser, Questionario, Pergunta, 
    Monitoramento, Resposta, TipoProblema, RelatoProblema
)

class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 1
    fields = ('texto', 'ordem', 'tipo_resposta')
    ordering = ('ordem',)

class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    fields = ('pergunta', 'resposta_sn', 'resposta_num', 'resposta_texto', 'foto')
    readonly_fields = ('pergunta',)
    
    def has_add_permission(self, request, obj):
        return False  # Impede adição de novas respostas diretamente no admin

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'inep', 'email_escola', 'funcao_monitoramento')
    search_fields = ('nome', 'inep', 'email_escola')
    list_filter = ('funcao_monitoramento',)

@admin.register(GREUser)
class GREUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'setor', 'escola', 'cargo', 'is_gestor', 'is_gre')
    list_filter = ('setor', 'escola')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cargo')
    readonly_fields = ('is_gestor', 'is_gre')
    
    def is_gestor(self, obj):
        return obj.is_gestor()
    is_gestor.boolean = True
    
    def is_gre(self, obj):
        return obj.is_gre()
    is_gre.boolean = True

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

class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    readonly_fields = ('pergunta', 'resposta_sn', 'resposta_num', 'resposta_texto', 'foto')
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(Monitoramento)
class MonitoramentoAdmin(admin.ModelAdmin):
    list_display = ('questionario', 'escola', 'data_envio', 'data_resposta', 'status', 'respondido_por')
    list_filter = ('questionario__setor', 'status', 'escola', 'data_envio')
    search_fields = ('escola__nome', 'questionario__titulo', 'respondido_por__user__username')
    date_hierarchy = 'data_envio'
    inlines = [RespostaInline]
    readonly_fields = ('data_envio', 'data_resposta')
    actions = ['marcar_como_resolvido', 'marcar_como_urgente']
    
    def marcar_como_resolvido(self, request, queryset):
        queryset.update(status='R', data_resposta=timezone.now())
    marcar_como_resolvido.short_description = "Marcar selecionados como Resolvidos"
    
    def marcar_como_urgente(self, request, queryset):
        queryset.update(status='U')
    marcar_como_urgente.short_description = "Marcar selecionados como Urgentes"

@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display = ('monitoramento', 'pergunta', 'resposta_formatada')
    list_filter = ('monitoramento__questionario__setor', 'monitoramento__escola')
    search_fields = ('pergunta__texto', 'monitoramento__escola__nome')
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
    list_display = ('tipo_problema', 'gestor', 'escola', 'data_relato', 'status', 'responsavel')
    list_filter = ('tipo_problema__setor', 'status', 'data_relato')
    search_fields = ('gestor__user__username', 'tipo_problema__descricao', 'descricao_adicional')
    date_hierarchy = 'data_relato'
    readonly_fields = ('data_relato',)
    actions = ['marcar_como_resolvido', 'marcar_como_urgente']
    
    def escola(self, obj):
        return obj.gestor.escola if obj.gestor.escola else '-'
    escola.short_description = 'Escola'
    
    def marcar_como_resolvido(self, request, queryset):
        queryset.update(status='R', data_resolucao=timezone.now())
    marcar_como_resolvido.short_description = "Marcar selecionados como Resolvidos"
    
    def marcar_como_urgente(self, request, queryset):
        queryset.update(status='U')
    marcar_como_urgente.short_description = "Marcar selecionados como Urgentes"