from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import *
from .serializers import *

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def verificar_acesso_monitor(view_func):
    """Decorator para verificar se usuário é monitor"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.greuser.is_monitor():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def verificar_acesso_gestor(view_func):
    """Decorator para verificar se usuário é gestor"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.greuser.is_gestor():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def verificar_acesso_setor(setor_requerido):
    """Decorator para verificar acesso a um setor específico"""
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.greuser.is_tecnico_gre() or not request.user.greuser.pode_acessar_setor(setor_requerido):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator



class EscolaViewSet(viewsets.ModelViewSet):
    queryset = Escola.objects.all()
    serializer_class = EscolaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def monitoramentos(self, request, pk=None):
        escola = self.get_object()
        monitoramentos = Monitoramento.objects.filter(escola=escola)
        serializer = MonitoramentoSerializer(monitoramentos, many=True)
        return Response(serializer.data)

class SetorViewSet(viewsets.ModelViewSet):
    queryset = Setor.objects.all()
    serializer_class = SetorSerializer
    permission_classes = [permissions.IsAuthenticated]

class GREUserViewSet(viewsets.ModelViewSet):
    queryset = GREUser.objects.all()
    serializer_class = GREUserSerializer
    permission_classes = [permissions.IsAdminUser]

class QuestionarioViewSet(viewsets.ModelViewSet):
    queryset = Questionario.objects.all()
    serializer_class = QuestionarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(setor=self.request.user.greuser.setor)

class PerguntaViewSet(viewsets.ModelViewSet):
    serializer_class = PerguntaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pergunta.objects.filter(questionario_id=self.kwargs['questionario_pk'])

    def perform_create(self, serializer):
        questionario = Questionario.objects.get(pk=self.kwargs['questionario_pk'])
        serializer.save(questionario=questionario)

class MonitoramentoViewSet(viewsets.ModelViewSet):
    queryset = Monitoramento.objects.all()
    serializer_class = MonitoramentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        if user.is_admin() or user.is_coordenador():
            return Monitoramento.objects.all()
        return Monitoramento.objects.filter(escola__in=user.escolas.all())

class RespostaViewSet(viewsets.ModelViewSet):
    serializer_class = RespostaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resposta.objects.filter(
            monitoramento_id=self.kwargs['monitoramento_pk']
        )

    def perform_create(self, serializer):
        monitoramento = Monitoramento.objects.get(pk=self.kwargs['monitoramento_pk'])
        serializer.save(
            monitoramento=monitoramento,
            respondido_por=self.request.user.greuser
        )

class TipoProblemaViewSet(viewsets.ModelViewSet):
    queryset = TipoProblema.objects.all()
    serializer_class = TipoProblemaSerializer
    permission_classes = [permissions.IsAuthenticated]

class RelatoProblemaViewSet(viewsets.ModelViewSet):
    serializer_class = RelatoProblemaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Adicione esta linha para resolver o erro
    queryset = RelatoProblema.objects.none()  # Valor inicial vazio
    
    def get_queryset(self):
        # Sobrescreve o queryset padrão
        return RelatoProblema.objects.filter(gestor=self.request.user.greuser)

    def perform_create(self, serializer):
        serializer.save(gestor=self.request.user.greuser)

from rest_framework.views import APIView
from rest_framework.response import Response

class MinhasEscolasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user.greuser
        escolas = user.escolas.all()
        serializer = EscolaSerializer(escolas, many=True)
        return Response(serializer.data)
    
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.db.models import Count, Q
from .models import Monitoramento, RelatoProblema, Questionario

def dashboard_monitoramentos(request):
    user = request.user.greuser
    context = {'section': 'dashboard_monitoramentos'}
    
    # Filtros baseados no tipo de usuário
    if user.is_admin() or user.is_coordenador():
        monitoramentos = Monitoramento.objects.all()
        problemas = RelatoProblema.objects.all()
    elif user.is_chefe_setor():
        monitoramentos = Monitoramento.objects.filter(escola__setor=user.setor)
        problemas = RelatoProblema.objects.filter(tipo_problema__setor=user.setor)
    else:
        monitoramentos = Monitoramento.objects.filter(escola__in=user.escolas.all())
        problemas = RelatoProblema.objects.filter(gestor=user)

    # Estatísticas
    total_monitoramentos = monitoramentos.count()
    monitoramentos_pendentes = monitoramentos.filter(status='P').count()
    problemas_urgentes = problemas.filter(prioridade='U').count()

    # Gráfico de status
    status_data = monitoramentos.values('status').annotate(total=Count('status'))
    status_labels = [dict(Monitoramento.STATUS_CHOICES).get(item['status'], '') for item in status_data]
    status_values = [item['total'] for item in status_data]

    context.update({
        'total_monitoramentos': total_monitoramentos,
        'monitoramentos_pendentes': monitoramentos_pendentes,
        'problemas_urgentes': problemas_urgentes,
        'status_labels': status_labels,
        'status_values': status_values,
        'upcoming_monitoramentos': monitoramentos.order_by('-data_envio')[:5],
        'problemas_recentes': problemas.order_by('-data_relato')[:5]
    })
    
    return render(request, 'monitoramentos/dashboard_monitoramentos.html', context)



class RelatosProblemasView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user.greuser
        problemas = RelatoProblema.objects.all()

        if user.is_admin() or user.is_coordenador():
            problemas = problemas
        elif user.is_chefe_setor():
            problemas = problemas.filter(tipo_problema__setor=user.setor)
        else:
            problemas = problemas.filter(gestor=user)

        return render(request, 'monitoramentos/relatos.html', {
            'problemas': problemas.order_by('-data_relato'),
            'prioridade_choices': dict(RelatoProblema.PRIORIDADE_CHOICES),
            'section': 'relatos_problemas'
        })

class DetalheMonitoramentoView(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        monitoramento = get_object_or_404(Monitoramento, pk=pk)
        if not request.user.greuser.pode_acessar_escola(monitoramento.escola):
            raise PermissionDenied

        return render(request, 'monitoramentos/detalhe.html', {
            'monitoramento': monitoramento,
            'respostas': monitoramento.respostas.all(),
            'status_choices': dict(Monitoramento.STATUS_CHOICES)
        })
    
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Setor, Questionario, Monitoramento

@login_required
def fluxo_monitoramento(request):
    # passo 1: puxar os setores que o usuário realmente tem permissão
    setores_permitidos = request.user.greuser.setores_permitidos()

    # passo 1.1: setor selecionado pela querystring
    setor_id = request.GET.get('setor')
    setor_selecionado = None
    if setor_id:
        setor_selecionado = get_object_or_404(Setor, pk=setor_id)

    # passo 2: questionário selecionado
    questionario_id = request.GET.get('questionario')
    questionario_selecionado = None
    if questionario_id:
        questionario_selecionado = get_object_or_404(Questionario, pk=questionario_id)

    # passo 3: últimos monitoramentos (limitado a 10)
    monitoramentos = []
    if questionario_selecionado:
        monitoramentos = (
            Monitoramento.objects
            .filter(questionario=questionario_selecionado)
            .order_by('-data_envio')[:10]
        )

    return render(request, 'monitoramentos/fluxo_monitoramento_setores.html', {
        'setores_permitidos': setores_permitidos,
        'setor_selecionado': setor_selecionado,
        'questionario_selecionado': questionario_selecionado,
        'monitoramentos': monitoramentos,
    })
