# REST Framework
from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer  # Importação do JSONRenderer


# Django
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, View, CreateView
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count


# App interno
from .models import *
from .serializers import *



# View auxiliar que retorna as escolas relacionadas a um questionário específico
class QuestionarioEscolasView(APIView):
    def get(self, request, pk):
        questionario = get_object_or_404(Questionario, pk=pk)
        escolas = questionario.escolas_destino.all()
        serializer = EscolaSerializer(escolas, many=True)
        return Response(serializer.data)
    
# View auxiliar que retorna os questionários e perguntas
class QuestionarioViewSet(viewsets.ModelViewSet):
    queryset = Questionario.objects.all()
    serializer_class = QuestionarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(setor=self.request.user.greuser.setor)


class PerguntaViewSet(viewsets.ModelViewSet):
    serializer_class = PerguntaSerializer
    filter_backends = [filters.OrderingFilter]  # Adicione esta linha
    ordering_fields = ['ordem']  # E esta linha
    
    def get_queryset(self):
        return Pergunta.objects.filter(
            questionario_id=self.kwargs['questionario_pk']
        ).order_by('ordem')
    
    def perform_create(self, serializer):
        serializer.save(
            questionario_id=self.kwargs['questionario_pk']
        )
        

# Paginação personalizada para escolas
class EscolaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

#Escolas, Setores e Usuários GRE
class EscolaViewSet(viewsets.ModelViewSet):
    queryset = Escola.objects.all().order_by('nome')
    serializer_class = EscolaSerializer
    pagination_class = EscolaPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'inep', 'endereco', 'nome_gestor']

    def get_serializer_context(self):
        return {'request': self.request}


class SetorViewSet(viewsets.ModelViewSet):
    queryset = Setor.objects.all()
    serializer_class = SetorSerializer
    permission_classes = [permissions.IsAuthenticated]

class GREUserViewSet(viewsets.ModelViewSet):
    queryset = GREUser.objects.all()
    serializer_class = GREUserSerializer
    permission_classes = [permissions.IsAdminUser]


#Monitoramentos e respostas
class MonitoramentoViewSet(viewsets.ModelViewSet):
    queryset = Monitoramento.objects.all()
    serializer_class = MonitoramentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        queryset = super().get_queryset()
        
        if user.is_admin() or user.is_coordenador():
            return queryset
        
        if user.is_chefe_setor():
            return queryset.filter(
                questionario__setor__in=user.setor.sub_setores.all() | Setor.objects.filter(id=user.setor.id)
            )
        
        return queryset.filter(escola__in=user.escolas.all())
    
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




class DetalheMonitoramentoView(DetailView):
    model = Monitoramento
    template_name = 'monitoramentos/detalhe_monitoramento.html'
    context_object_name = 'monitoramento'

    def get_queryset(self):
        user = self.request.user.greuser
        queryset = super().get_queryset()
        
        if user.is_admin() or user.is_coordenador():
            return queryset
        elif user.is_chefe_setor():
            return queryset.filter(questionario__setor__in=user.setores_permitidos())
        else:
            return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitoramento = self.get_object()
        
        # Obter todas as respostas ordenadas pela ordem das perguntas
        respostas = Resposta.objects.filter(
            monitoramento=monitoramento
        ).select_related('pergunta').order_by('pergunta__ordem')
        
        context['respostas'] = respostas
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        user = request.user.greuser
        if not (user.is_admin() or user.is_coordenador() or user.is_chefe_setor()):
            raise PermissionDenied
            
        return super().dispatch(request, *args, **kwargs)



#Dashboard
def dashboard_monitoramentos(request):
    user = request.user.greuser

    # Escolas acessíveis
    if user.is_admin() or user.is_coordenador():
        escolas = Escola.objects.all()
    elif user.is_chefe_setor():
        escolas = Escola.objects.filter(
            questionario__setor__in=user.setores_permitidos()
        ).distinct()
    else:
        escolas = user.escolas.all()

    # Filtro por escola
    school_id = request.GET.get('school_id')
    questionarios = Questionario.objects.none()
    if school_id:
        escola = get_object_or_404(Escola, pk=school_id)
        questionarios = Questionario.objects.filter(escolas_destino=escola)

    # Estatísticas
    monitoramentos = Monitoramento.objects.filter(escola__in=escolas)
    total_monitoramentos = monitoramentos.count()

    # Contar monitoramentos sem respostas
    monitoramentos_pendentes = monitoramentos.annotate(
        num_respostas=Count('respostas')
    ).filter(num_respostas=0).count()

    # Últimos monitoramentos
    upcoming_monitoramentos = monitoramentos.order_by('-id')[:5]

    context = {
        'escolas': escolas,
        'questionarios': questionarios,
        'selected_school': int(school_id) if school_id else None,
        'total_monitoramentos': total_monitoramentos,
        'monitoramentos_pendentes': monitoramentos_pendentes,
        'upcoming_monitoramentos': upcoming_monitoramentos,
        'status_labels': ['Respondidos', 'Pendentes'],
        'status_values': [
            total_monitoramentos - monitoramentos_pendentes,
            monitoramentos_pendentes
        ]
    }

    return render(request, 'monitoramentos/dashboard_monitoramentos.html', context)



    

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
           .order_by('-criado_em')[:10]
        )

    return render(request, 'monitoramentos/fluxo_monitoramento_setores.html', {
        'setores_permitidos': setores_permitidos,
        'setor_selecionado': setor_selecionado,
        'questionario_selecionado': questionario_selecionado,
        'monitoramentos': monitoramentos,
    })


class AdicionarQuestionarioView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def post(self, request):
        # Adiciona o usuário autenticado ao contexto
        serializer = QuestionarioSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Questionário e monitoramentos criados com sucesso!'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                'success': False,
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        ) 


from django.views.generic import DetailView
from django.urls import reverse

class GerenciarPerguntasView(DetailView):
    model = Questionario
    template_name = 'monitoramentos/gerenciar_perguntas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perguntas_api_url'] = reverse(
            'questionario-perguntas-list',
            kwargs={'questionario_pk': self.object.pk}
        )
        return context


from .serializers import QuestionarioSerializer

class QuestionarioCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionarioSerializer

from django.views.generic import ListView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

class SelecionarEscolaView(LoginRequiredMixin, ListView):
    model = Escola
    template_name = 'monitoramentos/selecionar_escola.html'
    context_object_name = 'escolas'
    paginate_by = 15  # ← Limita a 15 itens por página

    def get_queryset(self):
        qs = self.request.user.greuser.escolas.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q) |
                Q(inep__icontains=q) |
                Q(nome_gestor__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


from django.shortcuts import render, get_object_or_404

def criar_questionario_view(request, setor_id=None):
    user = request.user.greuser
    # busca o objeto Setor (ou 404 se não pertencer ao usuário)
    setores = user.setores_permitidos()
    setor_selecionado = None
    if setor_id:
        setor_selecionado = get_object_or_404(
            setores,  # garante que é permitido
            pk=setor_id
        )

    return render(request, 'monitoramentos/criar_questionario.html', {
        'setores_permitidos': setores,
        'setor_selecionado': setor_selecionado
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

class GerenciarQuestionariosView(LoginRequiredMixin, TemplateView):
    template_name = 'monitoramentos/gerenciar_questionarios.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user.greuser
        # Filtra questionários pelo setor do usuário
        context['questionarios'] = Questionario.objects.filter(
            setor__in=user.setores_permitidos()
        ).order_by('-data_criacao')
        return context
    

class QuestionariosEscolaView(LoginRequiredMixin, View):
    def get(self, request, escola_id):
        escola = get_object_or_404(Escola, id=escola_id)
        if not request.user.greuser.pode_acessar_escola(escola):
            raise PermissionDenied()

        questionarios = Questionario.objects.filter(
            escolas_destino=escola
        ).annotate(
            total_respostas=Count('monitoramentos'),
        ).prefetch_related('monitoramentos')

        hoje = timezone.now().date()
        total_hoje = 0
        ultima_resposta_geral = None
        
        for q in questionarios:
            q.respostas_hoje = Monitoramento.contagem_hoje(escola, q)
            total_hoje += q.respostas_hoje
            ultima = q.monitoramentos.order_by('-criado_em').first()
            if ultima and (not ultima_resposta_geral or ultima.criado_em > ultima_resposta_geral):
                ultima_resposta_geral = ultima.criado_em

        return render(request, 'monitoramentos/questionarios_escola.html', {
            'escola': escola,
            'questionarios': questionarios,
            'total_hoje': total_hoje,
            'total_geral': sum(q.total_respostas for q in questionarios),
            'ultima_resposta_geral': ultima_resposta_geral
        })
from django.shortcuts      import render, get_object_or_404
from django.views          import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models               import Escola, Questionario, Pergunta, Monitoramento
from .forms                import RespostaFormSet

class ResponderQuestionarioView(LoginRequiredMixin, View):
    template_name = 'monitoramentos/responder_questionario.html'

    def get(self, request, escola_id, questionario_id):
        escola      = get_object_or_404(Escola, id=escola_id)
        questionario = get_object_or_404(Questionario, id=questionario_id)
        perguntas   = Pergunta.objects.filter(questionario=questionario).order_by('ordem')

        formset = RespostaFormSet(
            perguntas=perguntas
        )

        return render(request, self.template_name, {
            'escola': escola,
            'questionario': questionario,
            'formset': formset,
            'hoje': timezone.now().date()  # Adicione esta linha
        })

    def post(self, request, escola_id, questionario_id):
        escola      = get_object_or_404(Escola, id=escola_id)
        questionario = get_object_or_404(Questionario, id=questionario_id)
        perguntas   = Pergunta.objects.filter(questionario=questionario).order_by('ordem')

        formset = RespostaFormSet(
            data=request.POST,
            files=request.FILES,
            perguntas=perguntas
        )

        if all(f.is_valid() for f in formset):
            foto = request.FILES.get('foto_comprovante')
            monitoramento = Monitoramento.objects.create(
                questionario=questionario,
                escola=escola,
                respondido_por=request.user,
                foto_comprovante=foto
            )
            for f in formset:
                resposta = f.save(commit=False)
                resposta.monitoramento = monitoramento
                resposta.save()
            return redirect('questionarios_escola', escola_id=escola_id)

        # se houver erros, volta pro form
       # Em caso de erro
        return render(request, self.template_name, {
            'escola': escola,
            'questionario': questionario,
            'formset': formset,
            'hoje': timezone.now().date(),  # Adicione esta linha
            'erro': 'Verifique os campos destacados'
        })


# Views relacionadas a problemas e escolas

class TipoProblemaViewSet(viewsets.ModelViewSet):
    queryset = TipoProblema.objects.all()
    serializer_class = TipoProblemaSerializer
    permission_classes = [permissions.IsAuthenticated]

class RelatoProblemaViewSet(viewsets.ModelViewSet):
    serializer_class = RelatoProblemaSerializer
    permission_classes = [permissions.IsAuthenticated]    
    
    queryset = RelatoProblema.objects.none()  # Valor inicial vazio
    
    def get_queryset(self):
        # Sobrescreve o queryset padrão
        return RelatoProblema.objects.filter(gestor=self.request.user.greuser)

    def perform_create(self, serializer):
        serializer.save(gestor=self.request.user.greuser)

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
from django.views.generic import CreateView
from django.urls import reverse_lazy

class RelatoProblemaCreateView(LoginRequiredMixin, CreateView):
    model = RelatoProblema
    fields = ['tipo_problema', 'descricao_adicional', 'prioridade', 'foto']
    template_name = 'escolas/relatar_problema.html'
    success_url = reverse_lazy('escola_dashboard')

    def form_valid(self, form):
        escola = self.request.user.greuser.escolas.first()
        form.instance.escola = escola
        form.instance.gestor = self.request.user.greuser
        return super().form_valid(form)
    
from rest_framework.views import APIView
from rest_framework.response import Response

class MinhasEscolasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user.greuser
        escolas = user.escolas.all()
        serializer = EscolaSerializer(escolas, many=True)
        return Response(serializer.data)
    
    from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escolas/escola_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user.greuser
        context['escola'] = user.escolas.first()
        context['relatos'] = RelatoProblema.objects.filter(
            escola=context['escola']
        ).order_by('-data_relato')[:5]
        return context