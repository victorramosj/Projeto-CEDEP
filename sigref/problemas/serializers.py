from rest_framework import serializers
from .models import Lacuna, ProblemaUsuario, AvisoImportante, STATUS_CHOICES
from monitoramento.models import Escola, Setor, GREUser
from monitoramento.serializers import EscolaSerializer, SetorSerializer, GREUserSerializer # Presume que esses existem

# --- Modificações nos Serializers ---

class LacunaSerializer(serializers.ModelSerializer):
    # Alterar escola para aceitar o ID da Escola na criação/atualização
    escola = serializers.PrimaryKeyRelatedField(queryset=Escola.objects.all(), write_only=True)
    escola_detalhes = EscolaSerializer(source='escola', read_only=True) # Para retornar os detalhes da escola na leitura

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Lacuna
        fields = [
            'id',
            'escola', # Campo para escrita (ID)
            'escola_detalhes', # Campo para leitura (detalhes do objeto)
            'disciplina',
            'carga_horaria',
            'criado_em',
            'status',
            'status_display'
        ]
        read_only_fields = ['criado_em', 'status_display'] # 'status' pode ser definido na criação se necessário, mas 'criado_em' é auto_now_add


class ProblemaUsuarioSerializer(serializers.ModelSerializer):
    # O usuário será definido automaticamente pela view, então 'usuario' deve ser read_only
    usuario = GREUserSerializer(read_only=True)
    
    # Alterar setor e escola para aceitar o ID do Setor/Escola na criação/atualização
    setor = serializers.PrimaryKeyRelatedField(queryset=Setor.objects.all(), allow_null=True, required=False, write_only=True)
    setor_detalhes = SetorSerializer(source='setor', read_only=True) # Para retornar os detalhes do setor na leitura

    escola = serializers.PrimaryKeyRelatedField(queryset=Escola.objects.all(), write_only=True)
    escola_detalhes = EscolaSerializer(source='escola', read_only=True) # Para retornar os detalhes da escola na leitura

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    anexo_url = serializers.SerializerMethodField()

    class Meta:
        model = ProblemaUsuario
        fields = [
            'id',
            'usuario', # Apenas para leitura
            'setor', # Campo para escrita (ID)
            'setor_detalhes', # Campo para leitura (detalhes do objeto)
            'descricao',
            'criado_em',
            'escola', # Campo para escrita (ID)
            'escola_detalhes', # Campo para leitura (detalhes do objeto)
            'status',
            'status_display',
            'anexo', # Campo para upload de arquivo
            'anexo_url'
        ]
        read_only_fields = ['criado_em', 'usuario', 'status_display'] # 'usuario' é read-only aqui porque será definido na view

    def get_anexo_url(self, obj):
        if obj.anexo and self.context.get('request'):
            return self.context['request'].build_absolute_uri(obj.anexo.url)
        return None

# AvisoImportanteSerializer não precisa de alterações para criar Lacunas/Problemas
# Ele seria usado se o app precisasse CRIAR avisos, o que não foi pedido explicitamente aqui.
class AvisoImportanteSerializer(serializers.ModelSerializer):
    setor_destino = SetorSerializer(read_only=True) # Para leitura
    escola = EscolaSerializer(read_only=True) # Para leitura
    criado_por = GREUserSerializer(read_only=True) # Para leitura

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
            'ativo',
            'imagem', # Certifique-se que o campo imagem está aqui se for para ser manipulado pela API
        ]
        read_only_fields = ['data_criacao']