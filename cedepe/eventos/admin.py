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
    list_display = ('evento', 'sala', 'inicio', 'fim')
    search_fields = ('evento__titulo', 'sala__nome')
    list_filter = ('sala', 'inicio', 'fim')
    
