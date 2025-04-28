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
            'celular': {'validators': [RegexValidator(regex=r'^\(\d{2}\) \d{5}-\d{4}$')]}
        }

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        gre_user = GREUser.objects.create(user=user, **validated_data)
        return gre_user

class PerguntaSerializer(serializers.ModelSerializer):
    tipo_resposta_display = serializers.CharField(source='get_tipo_resposta_display', read_only=True)

    class Meta:
        model = Pergunta
        fields = '__all__'
        read_only_fields = ['questionario']

from rest_framework import serializers
from .models import Questionario, Escola
from rest_framework.permissions import IsAuthenticated

class QuestionarioSerializer(serializers.ModelSerializer):
    permission_classes = [IsAuthenticated]
    escolas = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Escola.objects.all(),
        required=False
    )

    class Meta:
        model = Questionario
        fields = '__all__'
        extra_kwargs = {
            'criado_por': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['criado_por'] = self.context['request'].user
        return super().create(validated_data)

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

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Setor, Questionario, Monitoramento, Escola
from .serializers import EscolaSerializer, QuestionarioSerializer

@login_required
def fluxo_monitoramento(request):
    # passo 1: setores permitidos
    setores_permitidos = Setor.objects.filter(usuarios__in=[request.user.greuser]).distinct()

    # identificar setor selecionado
    setor_id = request.GET.get('setor')
    setor_selecionado = None
    if setor_id:
        setor_selecionado = get_object_or_404(Setor, pk=setor_id)

    # passo 2: questionário selecionado
    questionario_id = request.GET.get('questionario')
    questionario_selecionado = None
    if questionario_id:
        questionario_selecionado = get_object_or_404(Questionario, pk=questionario_id)

    # passo 3: últimos monitoramentos (para o questionário)
    monitoramentos = []
    if questionario_selecionado:
        monitoramentos = (
            Monitoramento.objects
            .filter(questionario=questionario_selecionado)
            .order_by('-data_envio')[:10]
        )

    return render(request, 'cedepe/fluxo_monitoramento_setores.html', {
        'setores_permitidos': setores_permitidos,
        'setor_selecionado': setor_selecionado,
        'questionario_selecionado': questionario_selecionado,
        'monitoramentos': monitoramentos,
    })


class AssignEscolasQuestionario(APIView):
    """
    GET: retorna todas as escolas e as já atribuídas ao questionário
    POST: recebe { "escolas": [1,2,3] } e atualiza questionario.escolas_destino
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        questionario = get_object_or_404(Questionario, pk=pk)
        todas = Escola.objects.all()
        serializer_todas = EscolaSerializer(todas, many=True, context={'request': request})
        assigned_ids = list(questionario.escolas_destino.values_list('pk', flat=True))
        return Response({
            'escolas': serializer_todas.data,
            'assigned': assigned_ids
        })

    def post(self, request, pk):
        questionario = get_object_or_404(Questionario, pk=pk)
        ids = request.data.get('escolas', [])
        # validação básica
        qs = Escola.objects.filter(pk__in=ids)
        questionario.escolas_destino.set(qs)
        questionario.save()
        # retorna o questionario serializado atualizado
        serializer = QuestionarioSerializer(questionario, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
