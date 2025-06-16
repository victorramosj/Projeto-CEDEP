from rest_framework import serializers
from .models import Lacuna, ProblemaUsuario, AvisoImportante
from monitoramento.models import Escola, Setor, GREUser
from monitoramento.serializers import EscolaSerializer, SetorSerializer, GREUserSerializer

class LacunaSerializer(serializers.ModelSerializer):
    escola = EscolaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Lacuna
        fields = [
            'id', 
            'escola', 
            'disciplina', 
            'carga_horaria', 
            'criado_em', 
            'status',
            'status_display'
        ]
        read_only_fields = ['criado_em']

class ProblemaUsuarioSerializer(serializers.ModelSerializer):
    usuario = GREUserSerializer(read_only=True)
    setor = SetorSerializer(read_only=True)
    escola = EscolaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    anexo_url = serializers.SerializerMethodField()

    class Meta:
        model = ProblemaUsuario
        fields = [
            'id',
            'usuario',
            'setor',
            'descricao',
            'criado_em',
            'escola',
            'status',
            'status_display',
            'anexo',
            'anexo_url'
        ]
        read_only_fields = ['criado_em']

    def get_anexo_url(self, obj):
        if obj.anexo:
            return self.context['request'].build_absolute_uri(obj.anexo.url)
        return None

class AvisoImportanteSerializer(serializers.ModelSerializer):
    setor_destino = SetorSerializer(read_only=True)
    escola = EscolaSerializer(read_only=True)
    criado_por = GREUserSerializer(read_only=True)
    
    class Meta:
        model = AvisoImportante
        fields = [
            'id',
            'setor_destino',
            'titulo',
            'mensagem',
            'prioridade',
            'escola',
            'criado_por',
            'data_criacao',
            'data_expiracao',
            'ativo'
        ]
        read_only_fields = ['data_criacao']