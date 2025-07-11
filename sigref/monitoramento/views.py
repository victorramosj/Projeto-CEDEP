# -----------------------------------------------------------------------------
# Imports do Python
# -----------------------------------------------------------------------------
import datetime
import json
from collections import Counter
from datetime import timedelta

# -----------------------------------------------------------------------------
# Imports de libs de terceiros (Numpy, Django, DRF)
# -----------------------------------------------------------------------------
import numpy as np
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q, Avg, Count, Max, Min, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DetailView, ListView, TemplateView,  View)
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

# -----------------------------------------------------------------------------
# Imports da aplicação local
# -----------------------------------------------------------------------------
from .forms import RespostaFormSet
from .models import (Escola, GREUser, Monitoramento, Pergunta, Questionario, Resposta, Setor)
from .serializers import QuestionarioSerializer, PerguntaSerializer, EscolaSerializer, SetorSerializer, GREUserSerializer, MonitoramentoSerializer, RespostaSerializer

# -----------------------------------------------------------------------------
# Imports de outros apps do projeto
# -----------------------------------------------------------------------------
from problemas.models import AvisoImportante, Lacuna, ProblemaUsuario




# -----------------------------------------------------------------------------
# View Questionário Escolas
# -----------------------------------------------------------------------------
# View auxiliar que retorna as escolas relacionadas a um questionário específico
class QuestionarioEscolasView(APIView):
    def get(self, request, pk):
        questionario = get_object_or_404(Questionario, pk=pk)
        escolas = questionario.escolas_destino.all()
        serializer = EscolaSerializer(escolas, many=True)
        return Response(serializer.data)

# -----------------------------------------------------------------------------
# View Questionário 
# -----------------------------------------------------------------------------
# View auxiliar que retorna os questionários e perguntas
class QuestionarioViewSet(viewsets.ModelViewSet):
    queryset = Questionario.objects.all()
    serializer_class = QuestionarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(setor=self.request.user.greuser.setor)

# -----------------------------------------------------------------------------
# View Perguntas
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# View Escola
# -----------------------------------------------------------------------------
# Paginação personalizada para escolas
class EscolaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# -----------------------------------------------------------------------------
# ViewSets para Escolas, Setores e Usuários GRE
# -----------------------------------------------------------------------------
#Escolas, Setores e Usuários GRE
class EscolaViewSet(viewsets.ModelViewSet):
    queryset = Escola.objects.all().order_by('nome')
    serializer_class = EscolaSerializer
    pagination_class = EscolaPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'inep', 'endereco', 'nome_gestor']

    @action(detail=False, methods=['get'])
    def all_ids(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        ids = queryset.values_list('id', flat=True)
        return Response({'ids': list(ids)})

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


# -----------------------------------------------------------------------------
# ViewSets para Monitoramentos e Respostas
# -----------------------------------------------------------------------------
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



# -----------------------------------------------------------------------------
# View para Detalhe do Monitoramento
# -----------------------------------------------------------------------------
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


def dashboard_monitoramentos(request):
    user = request.user.greuser

    # Período de filtro
    period = request.GET.get('period', '30')
    if period == 'custom':
        data_inicial_str = request.GET.get('data_inicial')
        data_final_str = request.GET.get('data_final')
        try:
            data_inicial = datetime.datetime.strptime(data_inicial_str, "%Y-%m-%d") if data_inicial_str else timezone.now() - timedelta(days=30)
            data_final = datetime.datetime.strptime(data_final_str, "%Y-%m-%d") if data_final_str else timezone.now()
        except ValueError:
            data_inicial = timezone.now() - timedelta(days=30)
            data_final = timezone.now()
    else:
        period_int = int(period)
        data_final = timezone.now()
        data_inicial = data_final - timedelta(days=period_int)
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

    # Estatísticas (agora filtrando por data)
    monitoramentos = Monitoramento.objects.filter(
        escola__in=escolas,
        criado_em__range=(data_inicial, data_final)
    )
    total_monitoramentos = monitoramentos.count()
    monitoramentos = Monitoramento.objects.filter(
        escola__in=escolas,
        criado_em__range=(data_inicial, data_final)
    )
    escolas_com_monitoramentos_ids = monitoramentos.values_list('escola_id', flat=True).distinct()
    escolas = escolas.filter(id__in=escolas_com_monitoramentos_ids)

    monitoramentos_por_escola = {
        escola_id: count
        for escola_id, count in monitoramentos.values('escola_id').annotate(total=Count('id')).values_list('escola_id', 'total')
    }

    monitoramentos_filtrados_por_escola = {}
    for escola in escolas:
        monitoramentos_filtrados_por_escola[escola.id] = list(
            monitoramentos.filter(escola=escola).order_by('-criado_em')[:3]
        )
    # Contar monitoramentos sem respostas
    monitoramentos_pendentes = monitoramentos.annotate(
        num_respostas=Count('respostas')
    ).filter(num_respostas=0).count()

    # Últimos monitoramentos
    upcoming_monitoramentos = monitoramentos.order_by('-id')[:5]

    # Obter setores com contagens (mantém igual)
    setores = Setor.objects.annotate(
        num_questionarios=Count('questionario'),
        num_monitoramentos=Count('questionario__monitoramentos')
    ).prefetch_related(
        Prefetch('questionario_set', queryset=Questionario.objects.annotate(
            num_monitoramentos=Count('monitoramentos')
        ))
    )

    # Obter monitoramentos recentes por setor (filtrando por data)
    monitoramentos_recentes = Monitoramento.objects.select_related(
        'escola', 'questionario'
    ).filter(criado_em__range=(data_inicial, data_final)).order_by('-criado_em')

    # Agrupar monitoramentos por setor
    monitoramentos_por_setor = {}
    for setor in setores:
        monitoramentos_por_setor[setor.id] = list(
            monitoramentos_recentes.filter(questionario__setor=setor)[:5]
        )

    for setor in setores:
        setor.monitoramentos_recentes = monitoramentos_por_setor.get(setor.id, [])

    greusers = GREUser.objects.all().select_related('user').order_by('nome_completo', 'user__username')
    greusers_info = [
        {
            'id': greuser.user.id,
            'nome_completo': greuser.nome_completo.strip() or (greuser.user.get_full_name() or greuser.user.username)
        }
        for greuser in greusers
    ]
    ver_todas = request.GET.get('ver_todas') == '1'

    # IDs das escolas filtradas
    escolas_ids = list(escolas.values_list('id', flat=True))

    # Problemas reportados no período e nessas escolas
    problemas = ProblemaUsuario.objects.filter(
        escola_id__in=escolas_ids,
        criado_em__range=(data_inicial, data_final)
    ).select_related('usuario', 'setor', 'escola')

    # Lacunas registradas no período e nessas escolas
    lacunas = Lacuna.objects.filter(
        escola_id__in=escolas_ids,
        criado_em__range=(data_inicial, data_final)
    ).select_related('escola')
    # Avisos importantes no período e nessas escolas
    avisos_importantes = AvisoImportante.objects.filter(
        escola_id__in=escolas_ids,
        data_criacao__range=(data_inicial, data_final)
    ).select_related('escola')

    problemas_pendentes = problemas.filter(status='P').count()
    context = {
        'escolas': escolas,
        'ver_todas': ver_todas,
        'monitoramentos_por_escola': monitoramentos_por_escola,
        'questionarios': questionarios,
        'selected_school': int(school_id) if school_id else None,
        'total_monitoramentos': total_monitoramentos,
        'monitoramentos_pendentes': monitoramentos_pendentes,
        'monitoramentos_filtrados_por_escola': monitoramentos_filtrados_por_escola,
        'upcoming_monitoramentos': upcoming_monitoramentos,
        'status_labels': ['Respondidos', 'Pendentes'],
        'status_values': [
            total_monitoramentos - monitoramentos_pendentes,
            monitoramentos_pendentes
        ],
        'setores': setores,
        'greusers': greusers_info,
        'period': period,
        # Adicionados:
        'problemas': problemas,
        'lacunas': lacunas,
        'problemas_pendentes': problemas_pendentes,
        'avisos_importantes': avisos_importantes,
    }
    

    return render(request, 'monitoramentos/dashboard_monitoramentos.html', context)
    
# -----------------------------------------------------------------------------
# Fluxo de Monitoramento
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# View para adicionar um novo questionário e seus monitoramentos
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# View para gerenciar perguntas de um questionário específico
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# View para criar um novo questionário
# -----------------------------------------------------------------------------

class QuestionarioCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionarioSerializer


# -----------------------------------------------------------------------------
# View para selecionar escola
# -----------------------------------------------------------------------------

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
        ctx['setores'] = Setor.objects.all().order_by('nome')
        return ctx

# -----------------------------------------------------------------------------
# View para criar um questionário
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# View para listar questionários de uma escola específica
# -----------------------------------------------------------------------------
class QuestionariosEscolaView(LoginRequiredMixin, View):
    def get(self, request, escola_id):
        escola = get_object_or_404(Escola, id=escola_id)
        user = request.user
        if not user.greuser.pode_acessar_escola(escola):
            raise PermissionDenied()

        # Obtém o intervalo do dia atual no fuso horário local
        agora = timezone.localtime(timezone.now())
        inicio_hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_hoje = agora.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Monitoramentos do usuário logado
        meus_monitoramentos = Monitoramento.objects.filter(
            escola=escola,
            respondido_por=user
        )
        
        meus_monitoramentos_hoje = meus_monitoramentos.filter(
            criado_em__range=(inicio_hoje, fim_hoje)
        ).count()
        
        meus_monitoramentos_total = meus_monitoramentos.count()
        
        # Setores que o usuário já respondeu questionários HOJE
        setores_respondidos_hoje = Setor.objects.filter(
            questionario__monitoramentos__escola=escola,
            questionario__monitoramentos__respondido_por=user,
            questionario__monitoramentos__criado_em__range=(inicio_hoje, fim_hoje)
        ).distinct()
        
        # Questionários que o usuário já respondeu HOJE
        questionarios_respondidos_hoje = Questionario.objects.filter(
            monitoramentos__escola=escola,
            monitoramentos__respondido_por=user,
            monitoramentos__criado_em__range=(inicio_hoje, fim_hoje)
        ).distinct()
        
        # Filtra os questionários da escola
        questionarios = Questionario.objects.filter(
            escolas_destino=escola
        ).annotate(
            total_respostas=Count('monitoramentos'),
            respostas_hoje=Count(
                'monitoramentos', 
                filter=Q(monitoramentos__criado_em__range=(inicio_hoje, fim_hoje))
            )
        )
        
        total_hoje = sum(q.respostas_hoje for q in questionarios)
        total_geral = sum(q.total_respostas for q in questionarios)
        
        ultima_resposta_geral = Monitoramento.objects.filter(
            escola=escola
        ).order_by('-criado_em').values_list('criado_em', flat=True).first()

        return render(request, 'monitoramentos/questionarios_escola.html', {
            'escola': escola,
            'questionarios': questionarios,
            'total_hoje': total_hoje,
            'total_geral': total_geral,
            'ultima_resposta_geral': ultima_resposta_geral,
            'hoje': agora.date(),
            'meus_monitoramentos_hoje': meus_monitoramentos_hoje,
            'meus_monitoramentos_total': meus_monitoramentos_total,
            'setores_respondidos': setores_respondidos_hoje,
            'questionarios_respondidos': questionarios_respondidos_hoje
        })
    

# -----------------------------------------------------------------------------
# View para responder questionário
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# View para visualizar gráficos de um questionário
# -----------------------------------------------------------------------------   
def visualizar_graficos_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)
    # Ordenar perguntas para exibição consistente
    perguntas = questionario.pergunta_set.all().order_by('ordem')

    dados_graficos = []

    for pergunta in perguntas:
        respostas = Resposta.objects.filter(pergunta=pergunta)
        tipo = pergunta.tipo_resposta
        dados = {}
        total_respostas = respostas.count()

        if tipo == 'SN':
            # Contagem de 'S' e 'N' diretamente no QuerySet para eficiência
            contagem_sn = respostas.aggregate(
                total_sim=Count('id', filter=models.Q(resposta_sn='S')),
                total_nao=Count('id', filter=models.Q(resposta_sn='N'))
            )
            total_sim = contagem_sn['total_sim'] or 0
            total_nao = contagem_sn['total_nao'] or 0
            
            perc_sim = (total_sim / total_respostas * 100) if total_respostas else 0
            perc_nao = (total_nao / total_respostas * 100) if total_respostas else 0
            
            dados = {
                'labels': ['Sim', 'Não'],
                'values': [perc_sim, perc_nao],
                'total_respostas': total_respostas,
                'total_sim': total_sim,
                'total_nao': total_nao,
                'perc_sim': round(perc_sim, 1),
                'perc_nao': round(perc_nao, 1),
            }

        elif tipo == 'NU':
            valores = list(respostas.filter(resposta_num__isnull=False).values_list('resposta_num', flat=True))
            
            if valores:
                valores_np = np.array(valores)
                media = np.mean(valores_np).item()
                mediana = np.median(valores_np).item()
                minimo = np.min(valores_np).item()
                maximo = np.max(valores_np).item()
                desvio_padrao = np.std(valores_np).item()
            else:
                media = mediana = minimo = maximo = desvio_padrao = 0
                
            dados = {
                'valores': valores,
                'total_respostas': total_respostas,
                'media': round(media, 2), # Arredondar para 2 casas decimais
                'mediana': round(mediana, 2),
                'min': minimo,
                'max': maximo,
                'desvio_padrao': round(desvio_padrao, 2),
            }

        elif tipo == 'TX':
            exemplos = list(respostas.filter(resposta_texto__isnull=False).values_list('resposta_texto', flat=True))
            dados = {
                'exemplos': exemplos[:10],  # Limitar a 10 exemplos para não sobrecarregar
                'total_respostas': total_respostas,
            }

        dados_graficos.append({
            'pergunta': pergunta.texto,
            'tipo': tipo,
            'dados': dados
        })

    # Obter estatísticas gerais do questionário
    total_monitoramentos = Monitoramento.objects.filter(questionario=questionario).count()
    
    # Escolas respondentes e suas contagens
    # Incluindo 'escola__nome' para usar diretamente no template sem ter que iterar sobre objetos Escola
    escolas_respondentes_data = Monitoramento.objects.filter(
        questionario=questionario
    ).values('escola__nome').annotate(total=Count('id')).order_by('-total')

    # Para a lista de escolas no cabeçalho (apenas nomes únicos)
    escolas_unicas = Escola.objects.filter(
        monitoramentos__questionario=questionario
    ).distinct().values_list('nome', flat=True)


    context = {
        'questionario': questionario,
        'dados_graficos': json.dumps(dados_graficos, default=str), # json.dumps para passar ao JS
        'total_monitoramentos': total_monitoramentos,
        'escolas_respondentes': list(escolas_respondentes_data),
        'escolas': list(escolas_unicas), # Renomeado para evitar conflito e ser mais claro
        'dados_graficos_json': True if dados_graficos else False # Para controle no template
    }

    return render(request, 'graficos/graficos_questionario.html', context)

#Relatórios


# -----------------------------------------------------------------------------
# View para relatório diário de monitoramentos
# -----------------------------------------------------------------------------
class RelatorioDiarioView(View):
    def get(self, request, escola_id):
        escola = get_object_or_404(Escola, id=escola_id)
        user = request.user
        agora = timezone.localtime(timezone.now())
        hoje = agora.date()
        
        # Obtém o intervalo do dia atual no fuso horário local
        inicio_hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_hoje = agora.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Busca apenas os questionários respondidos HOJE pelo usuário logado na escola
        questionarios = Questionario.objects.filter(
            monitoramentos__escola=escola,
            monitoramentos__respondido_por=user,
            monitoramentos__criado_em__range=(inicio_hoje, fim_hoje)
        ).distinct().prefetch_related(
            Prefetch(
                'monitoramentos',
                queryset=Monitoramento.objects.filter(
                    criado_em__range=(inicio_hoje, fim_hoje),
                    respondido_por=user
                ).prefetch_related(
                    Prefetch(
                        'respostas',
                        queryset=Resposta.objects.select_related('pergunta').order_by('pergunta__ordem')
                    )
                ).order_by('criado_em')
            )
        ).order_by('setor__nome', 'titulo')
        
        # Calcula estatísticas para o relatório
        total_questionarios = questionarios.count()
        total_monitoramentos = Monitoramento.objects.filter(
            escola=escola,
            respondido_por=user,
            criado_em__range=(inicio_hoje, fim_hoje)
        ).count()
        
        setores_envolvidos = set()
        usuarios_envolvidos = set()
        
        for q in questionarios:
            setores_envolvidos.add(q.setor.nome)
            for m in q.monitoramentos.all():
                if m.respondido_por:
                    if m.respondido_por.greuser and m.respondido_por.greuser.nome_completo:
                        usuarios_envolvidos.add(m.respondido_por.greuser.nome_completo)
                    else:
                        usuarios_envolvidos.add(m.respondido_por.username)
        
        context = {
            'escola': escola,
            'data': hoje,
            'questionarios': questionarios,
            'total_questionarios': total_questionarios,
            'total_monitoramentos': total_monitoramentos,
            'setores_envolvidos': len(setores_envolvidos),
            'usuarios_envolvidos': usuarios_envolvidos,
        }
        
        return render(request, 'monitoramentos/relatorio.html', context)
    
# -----------------------------------------------------------------------------
# View para relatório de monitoramentos
# -----------------------------------------------------------------------------
# Relatório de monitoramentos/ ADICIONAR PROBLEMAS E LACUNAS 
class RelatorioMonitoramentosView(View):
    def get(self, request):
        escola_id = request.GET.get('escola_id')
        user_id = request.GET.get('user_id')
        setor_id = request.GET.get('setor_id')
        quantidade = int(request.GET.get('quantidade', 10))  # padrão: 10

        monitoramento_filter = Q()
        escola = None
        usuario = None
        setor = None

        if escola_id and str(escola_id).isdigit():
            escola = get_object_or_404(Escola, id=int(escola_id))
            monitoramento_filter &= Q(escola=escola)
        if user_id and str(user_id).isdigit():
            usuario = get_object_or_404(User, id=int(user_id))
            monitoramento_filter &= Q(respondido_por=usuario)
        if setor_id and str(setor_id).isdigit():
            setor = get_object_or_404(Setor, id=int(setor_id))
            monitoramento_filter &= Q(questionario__setor=setor)

        monitoramentos = Monitoramento.objects.filter(
            monitoramento_filter
        ).select_related('escola', 'questionario', 'respondido_por').order_by('-criado_em')[:quantidade]

        escolas_relacionadas = list({m.escola for m in monitoramentos if m.escola is not None})

        monitoramento_ids = monitoramentos.values_list('id', flat=True)
        questionario_ids = Monitoramento.objects.filter(
            id__in=monitoramento_ids
        ).values_list('questionario_id', flat=True).distinct()
        questionarios = Questionario.objects.filter(
            id__in=questionario_ids
        ).prefetch_related(
            Prefetch(
                'monitoramentos',
                queryset=Monitoramento.objects.filter(
                    id__in=monitoramento_ids
                ).prefetch_related(
                    Prefetch(
                        'respostas',
                        queryset=Resposta.objects.select_related('pergunta').order_by('pergunta__ordem')
                    )
                ).order_by('criado_em')
            )
        ).order_by('setor__nome', 'titulo')

        setores_envolvidos = set()
        usuarios_envolvidos = set()
        for q in questionarios:
            setores_envolvidos.add(q.setor.nome)
            for m in q.monitoramentos.all():
                if m.respondido_por:
                    if hasattr(m.respondido_por, 'greuser') and m.respondido_por.greuser.nome_completo:
                        usuarios_envolvidos.add(m.respondido_por.greuser.nome_completo)
                    else:
                        usuarios_envolvidos.add(m.respondido_por.username)

        # Para popular o select de setores no modal
        setores = Setor.objects.all().order_by('nome')

        context = {
            'escola': escola,
            'escolas_relacionadas': escolas_relacionadas,
            'usuario': usuario,
            'setor': setor,
            'setores': setores,
            'data': timezone.localdate(),
            'questionarios': questionarios,
            'total_questionarios': questionarios.count(),
            'total_monitoramentos': monitoramentos.count(),
            'setores_envolvidos': len(setores_envolvidos),
            'usuarios_envolvidos': usuarios_envolvidos,
            'quantidade': quantidade,
        }
        return render(request, 'monitoramentos/relatorio.html', context)
    
# -----------------------------------------------------------------------------
# View para buscar usuários GRE
# -----------------------------------------------------------------------------
def greuser_search(request):
    q = request.GET.get('q', '')
    users = GREUser.objects.filter(nome_completo__icontains=q).order_by('nome_completo')[:20]
    results = [
        {"id": u.user.id, "text": u.nome_completo or u.user.username}
        for u in users
    ]
    return JsonResponse({"results": results})
