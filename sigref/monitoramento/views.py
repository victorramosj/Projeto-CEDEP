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