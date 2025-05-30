from django.contrib import admin
from .models import (
    Lacuna, ProblemaUsuario, 
)

# Lacuna Admin
@admin.register(Lacuna)
class LacunaAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'carga_horaria', 'escola', 'criado_em')
    list_filter = ('escola',)
    search_fields = ('disciplina', 'escola__nome')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)

# ProblemaUsuario Admin
@admin.register(ProblemaUsuario)
class ProblemaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario_nome', 'setor_hierarquia', 'criado_em')
    list_filter = ('setor', 'usuario__tipo_usuario')
    search_fields = ('usuario__user__username', 'setor__nome', 'descricao')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)
    list_select_related = ('usuario__user', 'setor')

    def usuario_nome(self, obj):
        return obj.usuario.user.get_full_name()
    usuario_nome.short_description = 'Usuário'

    def setor_hierarquia(self, obj):
        return obj.setor.hierarquia_completa if obj.setor else 'Geral'
    setor_hierarquia.short_description = 'Setor'
