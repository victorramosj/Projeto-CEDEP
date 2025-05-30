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

    class Meta:
        model = Questionario
        fields = ['id', 'titulo', 'descricao', 'setor', 'perguntas', 'escolas_destino', 'criado_por']
        extra_kwargs = {
            'setor': {'required': True},
            'criado_por': {'read_only': True}
        }

    def create(self, validated_data):
        perguntas_data = validated_data.pop('perguntas')
        escolas_data = validated_data.pop('escolas_destino', [])
        
        questionario = Questionario.objects.create(
            **validated_data,
            criado_por=self.context['request'].user
        )
        
        for pergunta_data in perguntas_data:
            Pergunta.objects.create(
                questionario=questionario,
                **pergunta_data
            )
        
        questionario.escolas_destino.set(escolas_data)
        return questionario
from rest_framework import serializers
from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 2

class RespostaSerializer(serializers.ModelSerializer):
    resposta_formatada = serializers.SerializerMethodField()
    foto = serializers.ImageField(write_only=True, required=False)
    foto_url = serializers.ImageField(source='foto', read_only=True)

    class Meta:
        model = Resposta
        fields = '__all__'
        read_only_fields = ['monitoramento']

    def validate_foto(self, file):
        max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise ValidationError(f'Imagem muito grande: tamanho máximo de {MAX_IMAGE_SIZE_MB} MB.')
        return file

    def get_resposta_formatada(self, obj):
        return obj.resposta_formatada()

    def create(self, validated_data):
        # aqui tratamos a reutilização do arquivo, mas o storage customizado já faz tudo
        return super().create(validated_data)


class MonitoramentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    respostas = RespostaSerializer(many=True, required=False)

    class Meta:
        model = Monitoramento
        fields = '__all__'

    def create(self, validated_data):
        respostas_data = validated_data.pop('respostas', [])
        monitoramento = Monitoramento.objects.create(**validated_data)
        
        # Cria respostas associadas
        for resposta_data in respostas_data:
            Resposta.objects.create(
                monitoramento=monitoramento,
                **resposta_data
            )
        
        return monitoramento

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

