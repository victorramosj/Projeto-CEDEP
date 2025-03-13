from django.contrib import admin
from .models import Quarto, Cama, Hospede, Reserva

class CamaInline(admin.TabularInline):
    model = Cama
    extra = 0  # Exibe apenas os registros já existentes; ajuste se desejar formulários extras
    fields = ('identificacao', 'status', 'criado_em', 'atualizado_em')
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(Quarto)
class QuartoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'descricao', 'criado_em', 'atualizado_em', 'camas_disponiveis')
    inlines = [CamaInline]  # Permite gerenciar as camas diretamente na página do quarto
    search_fields = ('numero', 'descricao')
    ordering = ('numero',)

@admin.register(Cama)
class CamaAdmin(admin.ModelAdmin):
    list_display = ('identificacao', 'quarto', 'status', 'criado_em', 'atualizado_em')
    list_filter = ('status', 'quarto')
    search_fields = ('identificacao',)

@admin.register(Hospede)
class HospedeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email', 'telefone', 'criado_em')
    search_fields = ('nome', 'cpf', 'email')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('hospede', 'cama', 'data_checkin', 'data_checkout', 'status', 'criado_em')
    list_filter = ('status', 'data_checkin', 'data_checkout')
    search_fields = ('hospede__nome', 'cama__identificacao')
    date_hierarchy = 'data_checkin'
