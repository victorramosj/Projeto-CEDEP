
from django.contrib import admin
from .models import Lacuna, ProblemaUsuario

@admin.register(Lacuna)
class LacunaAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'escola', 'carga_horaria', 'criado_em')
    list_filter  = ('escola',)
    search_fields = ('disciplina',)

@admin.register(ProblemaUsuario)
class ProblemaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'setor', 'criado_em')
    list_filter  = ('setor', 'usuario')
    search_fields = ('descricao',)
