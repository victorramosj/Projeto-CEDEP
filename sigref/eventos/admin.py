from django.contrib import admin
from .models import Sala, Evento, Agendamento

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'capacidade', 'localizacao')
    search_fields = ('nome',)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'organizador', 'data_criacao')
    search_fields = ('titulo', 'organizador__username')
    list_filter = ('data_criacao',)

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('evento', 'listar_salas', 'inicio', 'fim')
    search_fields = ('evento__titulo', 'salas__nome')
    list_filter = ('salas', 'inicio', 'fim')
    filter_horizontal = ('salas',)  # facilita seleção de múltiplas salas no admin

    def listar_salas(self, obj):
        return ", ".join([sala.nome for sala in obj.salas.all()])
    listar_salas.short_description = 'Salas'
