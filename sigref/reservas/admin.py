from django.contrib import admin
from .models import Quarto, Cama, Hospede, Ocupacao, Reserva

class CamaInline(admin.TabularInline):
    model = Cama
    extra = 0
    fields = ('identificacao', 'status', 'criado_em', 'atualizado_em')
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(Quarto)
class QuartoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'descricao', 'criado_em', 'atualizado_em', 'camas_disponiveis')
    inlines = [CamaInline]
    search_fields = ('numero', 'descricao')
    ordering = ('numero',)

@admin.register(Cama)
class CamaAdmin(admin.ModelAdmin):
    list_display = ('identificacao', 'quarto', 'status', 'criado_em', 'atualizado_em')
    list_filter = ('status', 'quarto')
    search_fields = ('identificacao', 'quarto__numero')
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(Hospede)
class HospedeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email', 'telefone', 'endereco', 'instituicao', 'criado_em')
    search_fields = ('nome', 'cpf', 'email')
    readonly_fields = ('criado_em', 'atualizado_em')

@admin.register(Ocupacao)
class OcupacaoAdmin(admin.ModelAdmin):
    list_display = ('hospede', 'cama', 'data_checkin', 'data_checkout', 'status', 'criado_em')
    list_filter = ('status', 'cama__quarto', 'data_checkin')
    search_fields = ('hospede__nome', 'cama__identificacao')
    date_hierarchy = 'data_checkin'
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def save_model(self, request, obj, form, change):
        # Garante a atualização do status da cama
        super().save_model(request, obj, form, change)
        obj.cama.save()  # Salva alterações no status da cama

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('hospede', 'data_checkin', 'data_checkout', 'status', 'criado_em')
    list_filter = ('status', 'data_checkin')
    search_fields = ('hospede__nome', 'quarto__numero')
    date_hierarchy = 'data_checkin'
    readonly_fields = ('criado_em', 'atualizado_em')