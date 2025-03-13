from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Fornecedor, Departamento, Bem, Movimentacao, LogAlteracao

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)
    ordering = ("nome",)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj_cpf", "contato", "endereco")
    search_fields = ("nome", "cnpj_cpf")
    ordering = ("nome",)

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)

@admin.register(Bem)
class BemAdmin(admin.ModelAdmin):
    list_display = ("nome", "numero_patrimonio", "categoria", "departamento", "status", "data_aquisicao", "valor", "fornecedor_display")
    search_fields = ("nome", "numero_patrimonio", "categoria__nome", "departamento__nome", "fornecedor__nome")
    list_filter = ("categoria", "departamento", "status")
    ordering = ("data_aquisicao",)
    actions = ["marcar_como_manutencao", "marcar_como_descartado"]

    def fornecedor_display(self, obj):
        return obj.fornecedor.nome if obj.fornecedor else "N/A"
    fornecedor_display.short_description = "Fornecedor"

    def marcar_como_manutencao(self, request, queryset):
        queryset.update(status="manutencao")
        self.message_user(request, "Os bens selecionados foram marcados como 'Em Manutenção'.")
    marcar_como_manutencao.short_description = "Marcar como 'Em Manutenção'"

    def marcar_como_descartado(self, request, queryset):
        queryset.update(status="descartado")
        self.message_user(request, "Os bens selecionados foram marcados como 'Descartado'.")
    marcar_como_descartado.short_description = "Marcar como 'Descartado'"

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("bem", "origem", "destino", "data_movimentacao", "responsavel_display")
    list_filter = ("origem", "destino", "data_movimentacao")
    search_fields = ("bem__nome", "origem__nome", "destino__nome", "responsavel__username")

    def responsavel_display(self, obj):
        return obj.responsavel.username if obj.responsavel else "Desconhecido"
    responsavel_display.short_description = "Responsável"

@admin.register(LogAlteracao)
class LogAlteracaoAdmin(admin.ModelAdmin):
    list_display = ("bem", "usuario", "data_alteracao", "descricao")
    search_fields = ("bem__nome", "usuario__username", "descricao")
    list_filter = ("data_alteracao",)
    ordering = ("-data_alteracao",)
