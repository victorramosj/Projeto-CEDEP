from django.contrib import admin
from .models import Lacuna, ProblemaUsuario, AvisoImportante

# ─────────────────────────────────────────────
# Lacuna Admin: exibe disciplina, carga horária, escola e data de criação
@admin.register(Lacuna)
class LacunaAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'carga_horaria', 'escola', 'criado_em')
    list_filter = ('escola',)
    search_fields = ('disciplina', 'escola__nome')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)


# ─────────────────────────────────────────────
# ProblemaUsuario Admin: exibe nome completo do GREUser, hierarquia do setor e data de criação
@admin.register(ProblemaUsuario)
class ProblemaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'setor_hierarquia', 'criado_em')
    list_filter = ('setor', 'usuario__tipo_usuario')
    search_fields = ('usuario__nome_completo', 'setor__nome', 'descricao')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)
    list_select_related = ('usuario__user', 'setor')

    def nome_completo(self, obj):
        # Exibe sempre o campo nome_completo do GREUser; se vazio, mostra username
        return obj.usuario.nome_completo or obj.usuario.user.username
    nome_completo.short_description = 'Usuário'
    nome_completo.admin_order_field = 'usuario__nome_completo'

    def setor_hierarquia(self, obj):
        return obj.setor.hierarquia_completa if obj.setor else 'Geral'
    setor_hierarquia.short_description = 'Setor'


from .models import AvisoImportante

# ─────────────────────────────────────────────
# AvisoImportante Admin: exibe título, escola, prioridade, status e expiração
@admin.register(AvisoImportante)
class AvisoImportanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'escola', 'prioridade', 'ativo', 'data_expiracao')
    list_filter = ('escola', 'prioridade', 'ativo')

    # remove o campo do formulário
    search_fields = ('titulo', 'mensagem')
    date_hierarchy = 'data_criacao'
    ordering = ('-data_criacao',)

    # Remover o campo criado_por do formulário; será preenchido automaticamente
    exclude = ('criado_por',)

    def save_model(self, request, obj, form, change):
        if not obj.criado_por_id:
            obj.criado_por = request.user.greuser
        super().save_model(request, obj, form, change)
