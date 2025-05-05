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

# serializers.py
class EscolaSerializer(serializers.ModelSerializer):
    foto_fachada_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Escola
        fields = ['id', 'nome', 'inep', 'endereco', 'foto_fachada_url', 
                 'nome_gestor', 'email_gestor', 'telefone']

    def get_foto_fachada_url(self, obj):
        if obj.foto_fachada:
            return self.context['request'].build_absolute_uri(obj.foto_fachada.url)
        return None

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
        extra_kwargs = {
            'texto': {'required': True},
            'tipo_resposta': {'required': True},
            'ordem': {'required': True}
        }

class QuestionarioSerializer(serializers.ModelSerializer):
    perguntas = PerguntaCreateSerializer(many=True, write_only=True)
    escolas_destino = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Escola.objects.all(),
        write_only=True
    )
    data_limite = serializers.DateField(write_only=True)  # Novo campo
    frequencia = serializers.CharField(write_only=True)    # Novo campo

    class Meta:
        model = Questionario
        fields = ['id', 'titulo', 'descricao', 'setor', 'perguntas', 
                 'escolas_destino', 'criado_por', 'data_limite', 'frequencia']
        extra_kwargs = {
            'setor': {'required': True},
            'criado_por': {'read_only': True}
        }

    def create(self, validated_data):
        # Extrai os dados específicos do monitoramento
        data_limite = validated_data.pop('data_limite')
        frequencia = validated_data.pop('frequencia')
        perguntas_data = validated_data.pop('perguntas')
        escolas_data = validated_data.pop('escolas_destino')
        
        # Cria o questionário
        questionario = Questionario.objects.create(
            **validated_data,
            criado_por=self.context['request'].user
        )
        
        # Cria as perguntas
        for pergunta_data in perguntas_data:
            Pergunta.objects.create(
                questionario=questionario,
                **pergunta_data
            )
        
        # Associa as escolas e cria os monitoramentos
        questionario.escolas_destino.set(escolas_data)
        
        # Cria um monitoramento para cada escola
        for escola in escolas_data:
            Monitoramento.objects.create(
                questionario=questionario,
                escola=escola,
                data_limite=data_limite,
                frequencia=frequencia
            )
        
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

