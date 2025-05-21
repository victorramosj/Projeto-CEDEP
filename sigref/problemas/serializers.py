from rest_framework import serializers
from .models import Lacuna, ProblemaUsuario

class LacunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lacuna
        fields = ['id', 'escola', 'disciplina', 'carga_horaria', 'criado_em']
        read_only_fields = ['criado_em']


class ProblemaUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemaUsuario
        fields = ['id', 'usuario', 'setor', 'descricao', 'criado_em']
        read_only_fields = ['usuario', 'criado_em']

