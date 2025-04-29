from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

class SetorSerializer(serializers.ModelSerializer):
    hierarquia_completa = serializers.SerializerMethodField()
    parent = serializers.StringRelatedField()
    sub_setores = serializers.SerializerMethodField()

    class Meta:
        model = Setor
        fields = '__all__'
    
    def get_hierarquia_completa(self, obj):
        return obj.hierarquia_completa
    
    def get_sub_setores(self, obj):
        return SetorSerializer(obj.sub_setores.all(), many=True).data

class EscolaSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False, allow_null=True)
    foto_fachada_url = serializers.ImageField(source='foto_fachada', read_only=True)

    class Meta:
        model = Escola
        fields = '__all__'
        extra_kwargs = {
            'telefone': {'validators': [RegexValidator(regex=r'^\(\d{2}\) \d{5}-\d{4}$')]},
            'telefone_gestor': {'validators': [RegexValidator(regex=r'^\(\d{2}\) \d{5}-\d{4}$')]}
        }

class GREUserSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    setor = serializers.PrimaryKeyRelatedField(queryset=Setor.objects.all(), allow_null=True)
    escolas = serializers.PrimaryKeyRelatedField(queryset=Escola.objects.all(), many=True)
    nivel_acesso = serializers.CharField(read_only=True)

    class Meta:
        model = GREUser
        fields = '__all__'
        extra_kwargs = {
            'cpf': {'validators': [RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')]},            
        }

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        gre_user = GREUser.objects.create(user=user, **validated_data)
        return gre_user



# serializers.py
class PerguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = '__all__'

class PerguntaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = ['texto', 'tipo_resposta', 'ordem']

# serializers.py

class QuestionarioSerializer(serializers.ModelSerializer):
    perguntas = PerguntaSerializer(many=True, read_only=True)
    escolas_destino = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Escola.objects.all(),
        write_only=True
    )

    class Meta:
        model = Questionario
        fields = ['id', 'titulo', 'descricao', 'setor', 'perguntas', 'escolas_destino']


class RespostaSerializer(serializers.ModelSerializer):
    resposta_formatada = serializers.SerializerMethodField()
    foto_url = serializers.ImageField(source='foto', read_only=True)

    class Meta:
        model = Resposta
        fields = '__all__'
        read_only_fields = ['monitoramento']

    def get_resposta_formatada(self, obj):
        return obj.resposta_formatada()

class MonitoramentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    frequencia_display = serializers.CharField(source='get_frequencia_display', read_only=True)
    respostas = RespostaSerializer(many=True, read_only=True)

    class Meta:
        model = Monitoramento
        fields = '__all__'

class TipoProblemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProblema
        fields = '__all__'

class RelatoProblemaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    foto_url = serializers.ImageField(source='foto', read_only=True)

    class Meta:
        model = RelatoProblema
        fields = '__all__'
        read_only_fields = ['data_relato', 'gestor']

