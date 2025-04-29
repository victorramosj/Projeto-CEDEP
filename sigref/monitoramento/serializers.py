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



class PerguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = ['texto', 'ordem', 'tipo_resposta']

class QuestionarioSerializer(serializers.ModelSerializer):
    setor = serializers.PrimaryKeyRelatedField(queryset=Setor.objects.all())
    perguntas = PerguntaSerializer(many=True)
    escolas = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Escola.objects.all()
    )

    class Meta:
        model = Questionario
        fields = ['id', 'titulo', 'descricao', 'setor', 'perguntas', 'escolas']
        extra_kwargs = {
            'setor': {'required': True}
        }

    def create(self, validated_data):
        # remove setor enviado pelo cliente
        validated_data.pop('setor', None)

        perguntas_data = validated_data.pop('perguntas')
        escolas_data  = validated_data.pop('escolas')

        # Cria o questionário usando o setor do usuário autenticado
        questionario = Questionario.objects.create(
            **validated_data,
            setor=self.context['request'].user.greuser.setor
        )

        # Cria perguntas
        Pergunta.objects.bulk_create([
            Pergunta(questionario=questionario, **p) for p in perguntas_data
        ])

        # Associa escolas e gera monitoramentos
        questionario.escolas_destino.set(escolas_data)
        Monitoramento.objects.bulk_create([
            Monitoramento(questionario=questionario, escola=escola)
            for escola in escolas_data
        ])

        return questionario



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

