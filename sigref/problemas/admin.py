
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

from .models import AvisoImportante

@admin.register(AvisoImportante)
class AvisoImportanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'escola', 'prioridade', 'ativo', 'data_expiracao')
    list_filter = ('escola', 'prioridade', 'ativo')

    # remove o campo do formulário
    exclude = ('criado_por',)

    def save_model(self, request, obj, form, change):
        if not obj.criado_por_id:
            obj.criado_por = request.user.greuser
        super().save_model(request, obj, form, change)
