from rest_framework import serializers
from .models import *


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'

class BemSerializer(serializers.ModelSerializer):
    # para leitura (quando retornar o objeto)
    categoria_detail = CategoriaSerializer(source='categoria', read_only=True)
    fornecedor_detail = FornecedorSerializer(source='fornecedor', read_only=True)
    departamento_detail = DepartamentoSerializer(source='departamento', read_only=True)
    
    # para escrita (aceitando apenas o ID)
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    fornecedor = serializers.PrimaryKeyRelatedField(queryset=Fornecedor.objects.all())
    departamento = serializers.PrimaryKeyRelatedField(queryset=Departamento.objects.all())

    class Meta:
        model = Bem
        fields = '__all__'


class MovimentacaoSerializer(serializers.ModelSerializer):
    bem = BemSerializer(read_only=True)
    origem = DepartamentoSerializer(read_only=True)
    destino = DepartamentoSerializer(read_only=True)

    class Meta:
        model = Movimentacao
        fields = '__all__'

class LogAlteracaoSerializer(serializers.ModelSerializer):
    bem = BemSerializer(read_only=True)
    usuario = serializers.StringRelatedField()

    class Meta:
        model = LogAlteracao
        fields = '__all__'
