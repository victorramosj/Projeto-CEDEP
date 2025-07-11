
# -----------------------------------------------------------------------------
# Imports do Python
# -----------------------------------------------------------------------------
import json
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Imports de libs de terceiros (Django, DRF, etc.)
# -----------------------------------------------------------------------------
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import (HttpResponse, HttpResponseForbidden,HttpResponseRedirect, JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.core.paginator import EmptyPage, PageNotAnInteger


from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# -----------------------------------------------------------------------------
# Imports da aplicação local
# -----------------------------------------------------------------------------
from monitoramento.models import Escola, GREUser, Setor

from .forms import AvisoForm, LacunaForm, ProblemaUsuarioForm
from .models import (AvisoImportante, ConfirmacaoAviso, Lacuna, ProblemaUsuario, STATUS_CHOICES)
from .serializers import (AvisoImportanteSerializer, LacunaSerializer, ProblemaUsuarioSerializer)

from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone
from datetime import timedelta
from .models import Escola, AvisoImportante # Certifique-se de que AvisoImportante está importado
from .models import Escola, AtualizacaoEscola
from .forms import AtualizacaoEscolaForm
# Em: problemas/views.py
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import AtualizacaoEscola


# Em: problemas/views.py

# ... suas outras importações ...
from django.db.models import Q # Garanta que o Q está importado
from .models import AtualizacaoEscola, AvisoImportante, ConfirmacaoAviso, Lacuna, ProblemaUsuario, Setor # Importe os modelos necessários
from .forms import ProblemaUsuarioForm, LacunaForm # Importe os forms necessários

# ... (outras views) ...
# =============================================================================
#  VIEW DA DASHBOARD
# =============================================================================

class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    """
    Exibe o painel principal para uma escola, com estatísticas, avisos
    e o status de solicitações de atualização.
    """
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser
        escola = None

        # Determina a escola a ser exibida
        if gre_user.is_escola():
            escola = gre_user.escolas.first()
        else:
            escola_id = self.kwargs.get('escola_id')
            if escola_id:
                escola = get_object_or_404(Escola, id=escola_id)

        # Se a escola não for encontrada, interrompe e retorna um erro
        if escola is None:
            context['error_message'] = "Escola não encontrada ou não associada ao usuário."
            return context

        # Busca a solicitação de atualização mais recente (pendente ou recusada)
        atualizacao_recente = AtualizacaoEscola.objects.filter(
            escola=escola,
            status__in=['pendente', 'recusado']
        ).order_by('-data_solicitacao').first()

        # --- LÓGICA DE AVISOS ATUALIZADA E CORRIGIDA ---
        # Busca avisos que:
        # 1. São para a escola específica OU são globais (escola=None)
        # 2. Estão marcados como 'ativo=True'
        # 3. A data de expiração está no futuro OU a data de expiração não foi definida (é nula)
        avisos_queryset = AvisoImportante.objects.filter(
            Q(escola=escola) | Q(escola__isnull=True),
            Q(ativo=True),
            # A nova condição que resolve o problema:
            Q(data_expiracao__gte=timezone.now()) | Q(data_expiracao__isnull=True)
        ).order_by('-prioridade', '-data_criacao').distinct()

        # Verifica quais avisos já foram visualizados pela escola
        avisos_visualizados_ids = set(ConfirmacaoAviso.objects.filter(
            escola=escola,
            status='visualizado'
        ).values_list('aviso_id', flat=True))

        for aviso in avisos_queryset:
            aviso.ja_visualizado = aviso.id in avisos_visualizados_ids

        # Coleta de estatísticas
        agora = timezone.now()
        lacunas_escola = Lacuna.objects.filter(escola=escola)
        problemas_escola = ProblemaUsuario.objects.filter(escola=escola)

        # Contexto final completo enviado ao template
        context.update({
            'gre_user': gre_user,
            'escola': escola,
            'atualizacao_recente': atualizacao_recente,
            'avisos': avisos_queryset,
            'setor': Setor.objects.all(),
            'form_problema': ProblemaUsuarioForm(),
            'form_lacuna': LacunaForm(),
            'total_lacunas': lacunas_escola.count(),
            'lacunas_resolvidas': lacunas_escola.filter(status='R').count(),
            'lacunas_pendentes': lacunas_escola.filter(status='P').count(),
            'lacunas_andamento': lacunas_escola.filter(status='E').count(),
            'lacunas_este_mes': lacunas_escola.filter(criado_em__month=agora.month, criado_em__year=agora.year).count(),
            'total_problemas': problemas_escola.count(),
            'problemas_resolvidos': problemas_escola.filter(status='R').count(),
            'problemas_pendentes': problemas_escola.filter(status='P').count(),
            'problemas_andamento': problemas_escola.filter(status='E').count(),
            'problemas_este_mes': problemas_escola.filter(criado_em__month=agora.month, criado_em__year=agora.year).count(),
        })

        return context

# =============================================================================
#  VIEW DA ATUALIZAÇÃO DE STATUS DA LACUNA
# =============================================================================
# Adicione estas importações se ainda não tiver
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
# Lembre-se de importar seus outros modelos, como AvisoImportante

class UpdateStatusLacuna(APIView):
    """
    Atualiza o status de uma lacuna e cria um aviso para a escola associada.
    """
    # Garante que o usuário esteja logado e usa autenticação de sessão
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, lacuna_id):
        lacuna = get_object_or_404(Lacuna, id=lacuna_id)
        
        # Pega todos os dados da requisição
        new_status = request.data.get('status')
        titulo_aviso = request.data.get('titulo')
        mensagem_aviso = request.data.get('mensagem')

        # Validação completa dos dados
        if not all([new_status, titulo_aviso, mensagem_aviso]):
            return Response(
                {"detail": "Dados incompletos. 'status', 'titulo' e 'mensagem' são obrigatórios."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        status_validos = [choice[0] for choice in Lacuna.STATUS_CHOICES]
        if new_status not in status_validos:
            return Response(
                {"detail": f"O status '{new_status}' é inválido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Atualiza o status da lacuna
        lacuna.status = new_status
        lacuna.save()

        # 2. Cria o Aviso Importante
        try:
            gre_user = getattr(request.user, 'greuser', None)
            if not gre_user:
                return Response(
                    {"detail": "Status atualizado, mas falha ao criar o aviso: Usuário logado não possui um perfil 'greuser' associado."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            AvisoImportante.objects.create(
                titulo=titulo_aviso,
                mensagem=mensagem_aviso,
                prioridade='normal',
                criado_por=gre_user,
                escola=lacuna.escola, # Usa a escola da lacuna
                ativo=True
            )
        except Exception as e:
            return Response(
                {"detail": f"Status atualizado, mas falha ao criar o aviso. Erro interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Status atualizado e aviso enviado com sucesso!"},
            status=status.HTTP_200_OK
        )


# =============================================================================
#  API PARA DELETAR LACUNAS
# =============================================================================
@require_POST
def deletar_lacunas_api(request):
    try:
        data = json.loads(request.body)
        lacuna_ids = data.get('ids', []) # <-- AQUI! Ela espera 'ids'
        
        if not lacuna_ids:
            return JsonResponse({'error': 'Nenhum ID de lacuna fornecido.'}, status=400)

        # Apagar as lacunas
        deleted_count, _ = Lacuna.objects.filter(id__in=lacuna_ids).delete()

        return JsonResponse({
            'message': f'{deleted_count} lacuna(s) apagada(s) com sucesso.',
            'deleted_ids': lacuna_ids
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
#  VIEW DA ATUALIZAÇÃO DE STATUS DO PROBLEMA
# =============================================================================
# problemas/views.py

# ...suas outras importações...
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication # <-- 1. IMPORTE AQUI

from .models import ProblemaUsuario, AvisoImportante
# ...

class UpdateStatusProblema(APIView):
    """
    Atualiza o status de um problema e cria um aviso para a escola associada.
    """
    # 2. ADICIONE AS DUAS LINHAS ABAIXO:
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, problema_id):
        # O resto da sua view continua exatamente igual...
        problema = get_object_or_404(ProblemaUsuario, id=problema_id)
        
        new_status = request.data.get('status')
        titulo_aviso = request.data.get('titulo')
        mensagem_aviso = request.data.get('mensagem')

        if not all([new_status, titulo_aviso, mensagem_aviso]):
            return Response(
                {"detail": "Dados incompletos. 'status', 'titulo' e 'mensagem' são obrigatórios."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        status_validos = [choice[0] for choice in ProblemaUsuario.STATUS_CHOICES]
        if new_status not in status_validos:
            return Response(
                {"detail": f"O status '{new_status}' é inválido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        problema.status = new_status
        problema.save()

        try:
            gre_user = getattr(request.user, 'greuser', None)
            if not gre_user:
                return Response(
                    {"detail": "Status atualizado, mas falha ao criar o aviso: Usuário logado não possui um perfil 'greuser' associado."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            AvisoImportante.objects.create(
                titulo=titulo_aviso,
                mensagem=mensagem_aviso,
                prioridade='normal',
                criado_por=gre_user,
                escola=problema.escola,
                ativo=True
            )
        except Exception as e:
            return Response(
                {"detail": f"Status atualizado, mas falha ao criar o aviso. Erro interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Status atualizado e aviso enviado com sucesso!"},
            status=status.HTTP_200_OK
        )

# =============================================================================
#  API PARA DELETAR PROBLEMAS
# =============================================================================
@require_POST
def deletar_problemas_api(request):
    try:
        data = json.loads(request.body)
        problema_ids = data.get('ids', []) # <-- AQUI! Ela espera 'ids'

        if not problema_ids:
            return JsonResponse({'error': 'Nenhum ID de problema fornecido.'}, status=400)

        # Apagar os problemas
        deleted_count, _ = ProblemaUsuario.objects.filter(id__in=problema_ids).delete()

        return JsonResponse({
            'message': f'{deleted_count} problema(s) apagado(s) com sucesso.',
            'deleted_ids': problema_ids
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =============================================================================
#  VIEWSETS PARA A API REST
# =============================================================================
class LacunaViewSet(viewsets.ModelViewSet):
    queryset = Lacuna.objects.all()
    serializer_class = LacunaSerializer

# =============================================================================
#  VIEW DO PROBLEMA USUÁRIO
# =============================================================================
class ProblemaUsuarioViewSet(viewsets.ModelViewSet):
    queryset = ProblemaUsuario.objects.all()
    serializer_class = ProblemaUsuarioSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}

# =============================================================================
#  VIEW DE AVISO IMPORTANTE
# =============================================================================
class AvisoImportanteViewSet(viewsets.ModelViewSet):
    queryset = AvisoImportante.objects.all()
    serializer_class = AvisoImportanteSerializer


# =============================================================================
#  VIEW DE RELATAR LACUNA
# =============================================================================
def relatar_lacuna_view(request, escola_id):
    escola = get_object_or_404(Escola, id=escola_id) 	# Obtém a escola com o ID da URL

    if request.method == 'POST':
        form = LacunaForm(request.POST)
        if form.is_valid():
            lacuna = form.save(commit=False)
            lacuna.escola = escola 	# Associa a lacuna à escola
            lacuna.save()
            return redirect('dashboard_escola', escola_id=escola.id) 	# Redireciona para o dashboard da escola
    else:
        form = LacunaForm()

    return render(request, 'escolas/relatar_lacuna.html', {'form': form, 'escola': escola})


# =============================================================================
#  VIEW DE RELATAR PROBLEMA
# =============================================================================
def relatar_problema_view(request, escola_id):
    escola = get_object_or_404(Escola,id= escola_id)
    # Verifica se o usuário está autenticado
    if request.method == 'POST':
        form = ProblemaUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            problema = form.save(commit=False)
            problema.usuario = request.user.greuser
            problema.escola = escola
            problema.save()
            return redirect('dashboard_escola', escola_id=escola.id)
    else:
        form = ProblemaUsuarioForm()
    return render(request, 'escolas/relatar_problema.html', {'form': form, 'escola': escola})


# =============================================================================
#  VIEW DO PROBLEMA DASHBOARD
# =============================================================================
def problema_dashboard_view(request):
    form = ProblemaUsuarioForm()
    return render(request, 'escolas/escola_dashboard.html', {'form': form}) 	# type: ignore


# =============================================================================
#  VIEW DA TELA LACUNA
# =============================================================================
@login_required
def tela_lacuna_view(request):
    # --- Bloco 1: Lógica de Permissão para Acesso à Página e ao Menu ---
    
    # Esta variável controlará se o link para "Lacunas" aparece no menu
    pode_ver_menu_lacunas = False
    
    # Primeiro, verificamos se o usuário é um superusuário.
    if request.user.is_superuser:
        pode_ver_menu_lacunas = True
    else:
        # Se não for, verificamos o setor de forma segura para evitar erros.
        # O hasattr previne falhas caso o usuário não tenha o perfil 'greuser' ou o setor.
        if hasattr(request.user, 'greuser') and request.user.greuser.setor:
            setor_nome = request.user.greuser.setor.nome.upper()
            # Lista de setores que podem ver o menu e acessar a página
            setores_permitidos = ['CGAF', 'UDP', 'ADM', 'ADMINISTRADOR'] 
            if setor_nome in setores_permitidos:
                pode_ver_menu_lacunas = True

    # Se o usuário não tem permissão, ele é redirecionado para a home.
    # Isso protege o acesso direto à URL /problemas/lacunas/
    if not pode_ver_menu_lacunas:
        return redirect('home')

    # --- Bloco 2: Lógica de Filtros e Paginação da Página ---
    
    lacunas_list = Lacuna.objects.select_related('escola').all()
    
    search_query = request.GET.get('q', '')
    data_filter = request.GET.get('data', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        lacunas_list = lacunas_list.filter(escola__nome__icontains=search_query)

    if data_filter == '1':
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(weeks=1))
    elif data_filter == '2':
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(days=30))
    elif data_filter == '3':
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(days=365))

    if status_filter:
        lacunas_list = lacunas_list.filter(status=status_filter)

    lacunas_list = lacunas_list.order_by('-criado_em')
    
    paginator = Paginator(lacunas_list, 8)
    page_number = request.GET.get('page')
    lacunas_page = paginator.get_page(page_number)

    # --- Bloco 3: Contexto para o Template ---

    context = {
        'lacunas_page': lacunas_page,
        'todas_lacunas': paginator.count,
        'search_query': search_query,
        'data_filter': data_filter,
        'status_filter': status_filter,
        'status_choices': STATUS_CHOICES,
        # A variável de permissão é enviada para o template.
        # Você usará {% if pode_ver_menu_lacunas %} no seu menu.
        'pode_ver_menu_lacunas': pode_ver_menu_lacunas,
    }

    return render(request, 'tela_lacunas.html', context)


# =============================================================================
#  VIEW DA TELA PROBLEMA
# =============================================================================
@login_required
def tela_problema_view(request):
    gre_user = request.user.greuser  # obtém o GREUser relacionado ao user

    # Obtém todos os setores que esse usuário tem permissão para acessar
    setores_permitidos = gre_user.setores_permitidos()

    # Começa filtrando só pelos setores permitidos
    problemas_list = ProblemaUsuario.objects.select_related('escola', 'usuario__user', 'setor') \
        .filter(setor__in=setores_permitidos)

    # Filtros opcionais
    escola_query = request.GET.get('escola', '')
    data_filter = request.GET.get('data', '')
    status_filter = request.GET.get('status', '')
    setor_filter = request.GET.get('setor', '')

    if escola_query:
        problemas_list = problemas_list.filter(escola__nome__icontains=escola_query)

    if data_filter == '1':
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(weeks=1))
    elif data_filter == '2':
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(days=30))
    elif data_filter == '3':
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(days=365))

    if status_filter:
        problemas_list = problemas_list.filter(status=status_filter)

    if setor_filter:
        # Garante que o setor filtrado também esteja entre os permitidos
        if setores_permitidos.filter(id=setor_filter).exists():
            problemas_list = problemas_list.filter(setor__id=setor_filter)
        else:
            problemas_list = problemas_list.none()  # impede acesso indevido

    todos_os_setores = setores_permitidos.order_by('nome')  # só os setores visíveis ao usuário

    paginator = Paginator(problemas_list, 6)
    page_number = request.GET.get('page')
    problemas_page = paginator.get_page(page_number)
    total_problemas = problemas_list.count()

    context = {
        'problemas_page': problemas_page,
        'total_problemas': total_problemas,
        'search_query': escola_query,
        'request': request,
        'status_choices': STATUS_CHOICES,
        'todos_os_setores': todos_os_setores,
    }

    return render(request, 'tela_problemas.html', context)


# =============================================================================
#  VIEWS DE AVISOS
# =============================================================================
@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser

    # --- FILTRAGEM INICIAL (DATABASE) ---
    if gre_user.is_admin():
        avisos_queryset = AvisoImportante.objects.select_related('escola', 'criado_por__user').all()
    else:
        avisos_queryset = AvisoImportante.objects.select_related('escola', 'criado_por__user').filter(criado_por=gre_user)

    #  NOVO: Recebe os parâmetros de filtro da URL
    prioridade_filtro = request.GET.get('prioridade', '')
    status_filtro = request.GET.get('status', '')
    escola_filtro = request.GET.get('q_escola', '')

    #  Aplica filtros que podem ser feitos no banco de dados
    if prioridade_filtro:
        avisos_queryset = avisos_queryset.filter(prioridade=prioridade_filtro)
    if escola_filtro:
        avisos_queryset = avisos_queryset.filter(escola__nome__icontains=escola_filtro)

    avisos_ordenados = list(avisos_queryset.order_by('-data_criacao'))

    # --- ANOTAÇÃO DE STATUS (PYTHON) ---
    confirmacoes = ConfirmacaoAviso.objects.filter(
        aviso__in=avisos_ordenados,
        status='visualizado'
    ).values('aviso_id')
    
    avisos_visualizados_ids = {conf['aviso_id'] for conf in confirmacoes}

    for aviso in avisos_ordenados:
        aviso.foi_visualizado = aviso.id in avisos_visualizados_ids

    #  NOVO: Aplica o filtro de status que depende da anotação em Python
    if status_filtro:
        if status_filtro == 'visualizado':
            avisos_ordenados = [aviso for aviso in avisos_ordenados if aviso.foi_visualizado]
        elif status_filtro == 'pendente':
            avisos_ordenados = [aviso for aviso in avisos_ordenados if not aviso.foi_visualizado]

    # --- PAGINAÇÃO ---
    paginator = Paginator(avisos_ordenados, 9)
    page_number = request.GET.get('page')
    avisos_paginated = paginator.get_page(page_number)

    # NOVO: Passa os filtros atuais de volta para o template
    context = {
        'avisos': avisos_paginated,
        'prioridade_atual': prioridade_filtro,
        'status_atual': status_filtro,
        'search_query': escola_filtro,
    }

    return render(request, 'problemas/listar_avisos.html', context)

# =============================================================================
#  VIEW DA CRIAÇÃO DE AVISO
# =============================================================================
@login_required
def criar_aviso_view(request):
    gre_user = request.user.greuser

    # Verifica se o usuário é do tipo 'Escola' e bloqueia o acesso
    if gre_user.is_escola():
        messages.error(request, "Usuários do tipo 'Escola' não têm permissão para criar avisos.")
        return redirect('listar_avisos')

    # Busca todas as escolas para preencher o formulário no método GET
    escolas = Escola.objects.all().order_by('nome')

    if request.method == 'POST':
        # --- Obtenção dos dados do formulário ---
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        prioridade = request.POST.get('prioridade', 'normal')
        data_expiracao_str = request.POST.get('data_expiracao')
        escolas_ids = request.POST.getlist('escola_id')
        
        #  Obtém o arquivo de imagem do request. Será 'None' se nenhum for enviado.
        imagem_aviso = request.FILES.get('imagem')

        # --- Validação dos dados ---
        if not titulo or not mensagem:
            messages.error(request, "O título e a mensagem são obrigatórios.")
            # Retorna ao formulário, mantendo os dados que o usuário já preencheu
            return render(request, 'avisos/criar_aviso.html', {
                'escolas': escolas,
                'request': request # Passa o request para popular os campos no template
            })

        if not escolas_ids:
            messages.error(request, "Pelo menos uma escola precisa ser selecionada.")
            return render(request, 'avisos/criar_aviso.html', {
                'escolas': escolas,
                'request': request
            })

        # --- Processamento dos dados ---
        data_expiracao = None
        if data_expiracao_str:
            try:
                # O formato do datetime-local do HTML é "YYYY-MM-DDTHH:MM"
                data_expiracao = timezone.datetime.strptime(data_expiracao_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                messages.error(request, "O formato da data de expiração é inválido.")
                return render(request, 'avisos/criar_aviso.html', {
                    'escolas': escolas,
                    'request': request
                })

        # --- Criação dos Avisos ---
        for escola_id in escolas_ids:
            try:
                escola = Escola.objects.get(id=escola_id)
                
                # Prepara um dicionário com os dados comuns
                dados_aviso = {
                    'titulo': titulo,
                    'mensagem': mensagem,
                    'prioridade': prioridade,
                    'criado_por': gre_user,
                    'escola': escola,
                    'ativo': True,
                    'data_expiracao': data_expiracao
                }

                # Adiciona a imagem ao dicionário SOMENTE se ela foi enviada
                if imagem_aviso:
                    dados_aviso['imagem'] = imagem_aviso

                # Cria o objeto no banco de dados usando os dados do dicionário
                AvisoImportante.objects.create(**dados_aviso)

            except Escola.DoesNotExist:
                messages.warning(request, f"A escola com ID {escola_id} não foi encontrada e foi ignorada.")
                continue

        messages.success(request, "Aviso(s) criado(s) com sucesso!")
        return redirect('listar_avisos')

    # Contexto para o método GET (quando a página é carregada pela primeira vez)
    context = {
        'escolas': escolas
    }
    return render(request, 'avisos/criar_aviso.html', context)

# =============================================================================
#  VIEW DA EDIÇÃO DE AVISO
# =============================================================================
@login_required
def editar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser

    # Verificação de permissão 
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        messages.error(request, "Você não tem permissão para editar este aviso.")
        return redirect('listar_avisos')

    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            #  Salva as alterações (título, mensagem, etc.) no aviso.
            aviso_editado = form.save()

            # Redefine o status de TODAS as confirmações associadas para 'pendente'.
            #    Esta é a única linha necessária para a nova lógica.
            aviso_editado.confirmacoes.all().update(status='pendente')

            messages.success(request, "Aviso editado com sucesso! O status das escolas que já tinham visualizado este aviso foi atualizado para 'Pendente'.")
            return redirect('listar_avisos')
        else:
            messages.error(request, "Houve um erro ao editar o aviso. Verifique os dados inseridos.")
            return redirect('listar_avisos')

    # Se a requisição for GET, apenas redireciona para a lista.
    return redirect('listar_avisos')

# =============================================================================
#  VIEW DA EXCLUSÃO DE AVISO
# =============================================================================
@login_required
def apagar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser

    # Verifica se o aviso foi criado pelo usuário ou se ele é administrador
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        messages.error(request, "Você não tem permissão para excluir este aviso.")
        return redirect('listar_avisos') 	# Redireciona para a página de avisos

    aviso.delete()
    messages.success(request, "Aviso excluído com sucesso!")
    return redirect('listar_avisos') 	# Redireciona para a lista de avisos após a exclusão

# =============================================================================
#  VIEW DA EXCLUSÃO DE VÁRIOS AVISOS
# =============================================================================
def apagar_varios_avisos(request):
    if request.method == 'POST':
        # Pega os IDs dos avisos selecionados
        avisos_selecionados = request.POST.getlist('avisos_selecionados')

        # Apagar os avisos selecionados
        if avisos_selecionados:
            AvisoImportante.objects.filter(id__in=avisos_selecionados).delete()
            messages.success(request, "Avisos apagados com sucesso!")
        else:
            messages.warning(request, "Nenhum aviso selecionado para apagar.")

    return redirect('listar_avisos')


# =============================================================================
#  VIEWS DE VERIFICAÇÃO/EXCLUSÃO AUTOMÁTICA DE AVISOS
# =============================================================================
def verificar_avisos_automaticos(request):
    """Verifica avisos que estão ativos mas cuja data de expiração já passou. Esta lógica é mais precisa, usando os campos do seu modelo."""
    # Filtra por avisos que ainda estão marcados como ativos
    # e cuja data de expiração já passou (é menor que o tempo atual).
    avisos_expirados = AvisoImportante.objects.filter(
        ativo=True,
        data_expiracao__isnull=False, # Garante que o campo de expiração não é nulo
        data_expiracao__lt=timezone.now()
    )
    
    # Prepara a lista de avisos para ser enviada como JSON
    avisos_para_apagar = list(avisos_expirados.values('id', 'titulo'))
    
    return JsonResponse({'avisos_para_apagar': avisos_para_apagar})

# =============================================================================
#  VIEW DA EXCLUSÃO DE AVISOS AUTOMÁTICOS
# =============================================================================
@require_POST
def apagar_avisos_automaticos(request):
    """Recebe uma lista de IDs de avisos via POST e os apaga. Esta função agora opera no modelo AvisoImportante. """
    try:
        data = json.loads(request.body)
        aviso_ids = data.get('aviso_ids', [])

        if not aviso_ids or not isinstance(aviso_ids, list):
            return JsonResponse({'status': 'error', 'message': 'Nenhum ID de aviso fornecido.'}, status=400)

        # Apaga os avisos do modelo correto: AvisoImportante
        avisos_apagados, _ = AvisoImportante.objects.filter(id__in=aviso_ids).delete()

        if avisos_apagados > 0:
            return JsonResponse({'status': 'success', 'message': f'{avisos_apagados} aviso(s) foram apagados com sucesso.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Nenhum aviso correspondente encontrado para apagar.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Formato de requisição inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# =============================================================================
#  VIEW DA DASHBOARD- CEDEPE(NOTIFICAÇÃO)
# =============================================================================
def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "cedepe/home.html")

    try:
        gre_user = request.user.greuser
        setor = gre_user.setor
        escolas = gre_user.escolas.all()

        # Filtrar lacunas apenas das escolas do usuário
        lacunas_pendentes = Lacuna.objects.filter(escola__in=escolas, status='P')
        # Filtrar problemas apenas do setor do usuário
        problemas_pendentes = ProblemaUsuario.objects.filter(setor=setor, status='P')

        alerts = []
        if lacunas_pendentes.exists():
            alerts.append({
                'type': 'lacuna',
                'count': lacunas_pendentes.count(),
                'url': 'tela_lacunas',
                'text': f"Você tem {lacunas_pendentes.count()} lacuna(s) pendente(s)."
            })
        if problemas_pendentes.exists():
            alerts.append({
                'type': 'problema',
                'count': problemas_pendentes.count(),
                'url': 'tela_problemas',
                'text': f"Você tem {problemas_pendentes.count()} problema(s) pendente(s)."
            })

        return render(request, "cedepe/home.html", {"alerts": alerts})

    except GREUser.DoesNotExist:
        
        return render(request, "cedepe/home.html")

# =============================================================================
#  VIEW DA CONFIRMAÇÃO DE VISUALIZAÇÃO DE AVISO
# =============================================================================
@login_required
def confirmar_visualizacao_aviso(request, aviso_id):
    # Garante que a requisição é do tipo POST
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)

    # Bloco de verificação de perfil e permissão
    try:
        gre_user = request.user.greuser
        if not gre_user.is_escola:
            return JsonResponse({'status': 'error', 'message': 'Apenas usuários de escolas podem visualizar avisos.'}, status=403)
        
        escola_do_usuario = gre_user.escolas.first()
        if not escola_do_usuario:
            return JsonResponse({'status': 'error', 'message': 'Usuário não está associado a nenhuma escola.'}, status=400)
            
    except (GREUser.DoesNotExist, AttributeError):
        return JsonResponse({'status': 'error', 'message': 'Perfil de usuário inválido ou não encontrado.'}, status=400)

    # Recupera o aviso ou retorna erro 404
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)

    # Busca ou cria o registro de confirmação.
    confirmacao, created = ConfirmacaoAviso.objects.get_or_create(
        aviso=aviso,
        escola=escola_do_usuario
    )

    # Altera o status se estiver pendente
    if confirmacao.status == 'pendente':
        confirmacao.confirmar_visualizado() # Chama o método do seu modelo
        return JsonResponse({'status': 'success', 'message': 'Aviso marcado como visualizado.'})
    
    # Se o status já era 'visualizado', apenas informa
    else:
        return JsonResponse({'status': 'already_viewed', 'message': 'Este aviso já havia sido visualizado.'})





# =============================================================================
#  VIEW PARA A EXIBIÇÃO DOS DETALHES DOS PROBLEMAS (COM PESQUISA)
# =============================================================================
def detalhes_problemas_view(request, escola_id):
    """ Esta view exibe uma lista detalhada de TODOS os problemas pertencentes a UMA escola específica."""
    escola = get_object_or_404(Escola, pk=escola_id)
    
    # Obter o termo de pesquisa a partir dos parâmetros da URL
    search_query = request.GET.get('q', '')

    # Iniciar a consulta base, filtrando pela escola
    lista_de_problemas = ProblemaUsuario.objects.filter(escola=escola).select_related('usuario__user', 'setor')

    # Aplicar o filtro de pesquisa, se um termo for fornecido
    if search_query:
        lista_de_problemas = lista_de_problemas.filter(
            Q(descricao__icontains=search_query) |
            Q(setor__nome__icontains=search_query) |
            Q(usuario__user__username__icontains=search_query) |
            Q(usuario__user__first_name__icontains=search_query) |
            Q(usuario__user__last_name__icontains=search_query)
        )

    # Ordenar o resultado final
    lista_de_problemas = lista_de_problemas.order_by('-criado_em')
    
    # Adiciona paginação para organizar a lista
    paginator = Paginator(lista_de_problemas, 8)
    page_number = request.GET.get('page')
    problemas_paginados = paginator.get_page(page_number) # .get_page lida com exceções

    # Envia os dados para o template, incluindo o termo de pesquisa
    context = {
        'escola': escola,
        'problemas': problemas_paginados,
        'search_query': search_query,
    }
    
    # Renderiza o template de detalhes
    return render(request, 'detalhes/detalhes_problemas.html', context)


# =============================================================================
#  VIEW PARA A EXIBIÇÃO DOS DETALHES DAS LACUNAS (COM PESQUISA)
# =============================================================================
def detalhes_lacunas_view(request, escola_id):
    """Esta view exibe uma lista detalhada de TODAS as lacunas pertencentes a UMA escola específica."""
    escola = get_object_or_404(Escola, pk=escola_id)
    
    # Obter o termo de pesquisa a partir dos parâmetros da URL
    search_query = request.GET.get('q', '')

    # Iniciar a consulta base, filtrando pela escola
    lista_de_lacunas = Lacuna.objects.filter(escola=escola)

    # Aplicar o filtro de pesquisa, se um termo for fornecido
    if search_query:
        lista_de_lacunas = lista_de_lacunas.filter(disciplina__icontains=search_query)

    # Ordenar o resultado final
    lista_de_lacunas = lista_de_lacunas.order_by('-criado_em')

    # Adiciona paginação
    paginator = Paginator(lista_de_lacunas, 8)
    page_number = request.GET.get('page')
    lacunas_paginadas = paginator.get_page(page_number)

    # Envia os dados para o template
    context = {
        'escola': escola,
        'lacunas': lacunas_paginadas,
        'search_query': search_query,
    }

    # Renderiza o template de detalhes
    return render(request, 'detalhes/detalhes_lacunas.html', context)


# =============================================================================
#  VIEW DA SOLICITAÇÃO DE ATUALIZAÇÃO DE DADOS DA ESCOLA
# =============================================================================


@login_required
def solicitar_atualizacao(request, escola_id):
    """
    Processa o POST do formulário de atualização de dados da escola.
    Cria uma nova instância de AtualizacaoEscola para validação.
    """
    # Garante que a escola referenciada na URL existe.
    escola = get_object_or_404(Escola, id=escola_id)

    # Esta view só deve processar dados via POST.
    if request.method == 'POST':
        # VERIFICAÇÃO: Não permite uma nova solicitação se uma já estiver pendente.
        if AtualizacaoEscola.objects.filter(escola=escola, status='pendente').exists():
            messages.error(request, 'Já existe uma solicitação de atualização pendente para esta escola.')
            return redirect('dashboard_escola', escola_id=escola.id)

        # Cria uma instância do formulário com os dados da requisição (POST) e os arquivos (FILES).
        form = AtualizacaoEscolaForm(request.POST, request.FILES)

        # Valida o formulário.
        if form.is_valid():
            # Cria o objeto de atualização em memória, sem salvar no banco ainda.
            atualizacao = form.save(commit=False)
            
            # Associa a solicitação à escola e ao usuário logado.
            atualizacao.escola = escola
            atualizacao.solicitado_por = request.user
            
            # Agora, salva o objeto no banco de dados.
            atualizacao.save()
            
            messages.success(request, 'Sua solicitação de atualização foi enviada com sucesso e aguarda validação.')
            return redirect('dashboard_escola', escola_id=escola.id)
        else:
            # Se o formulário for inválido, informa o usuário.
            messages.error(request, 'Houve um erro no formulário. Por favor, verifique os dados e tente novamente.')
    
    # Se o método não for POST (ex: alguém digitou a URL direto no navegador), redireciona.
    return redirect('dashboard_escola', escola_id=escola.id)


# NOVA VIEW PARA LISTAR SOLICITAÇÕES
class ListaValidacoesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AtualizacaoEscola
    template_name = 'problemas/lista_validacoes.html'  # Novo template que vamos criar
    context_object_name = 'solicitacoes'

    def test_func(self):
        # Apenas superusuários ou membros de um grupo específico podem ver esta página
        return self.request.user.is_superuser

    def get_queryset(self):
        # Retorna apenas as solicitações com status 'pendente'
        return AtualizacaoEscola.objects.filter(status='pendente').order_by('data_solicitacao')
    

class DetalheValidacaoView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AtualizacaoEscola
    template_name = 'problemas/detalhe_validacao.html'
    context_object_name = 'solicitacao'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['escola'] = self.get_object().escola
        return context

    def post(self, request, *args, **kwargs):
        solicitacao = self.get_object()
        escola = solicitacao.escola

        # Se o botão 'aprovar' foi clicado
        if 'aprovar' in request.POST:
            # ... (lógica de aprovação, que já está funcionando, permanece a mesma) ...
            if solicitacao.endereco:
                escola.endereco = solicitacao.endereco
            if solicitacao.telefone:
                escola.telefone = solicitacao.telefone
            if solicitacao.email_escola:
                escola.email_escola = solicitacao.email_escola
            if solicitacao.nome_gestor:
                escola.nome_gestor = solicitacao.nome_gestor
            if solicitacao.telefone_gestor:
                escola.telefone_gestor = solicitacao.telefone_gestor
            if solicitacao.email_gestor:
                escola.email_gestor = solicitacao.email_gestor
            if solicitacao.foto_fachada:
                escola.foto_fachada = solicitacao.foto_fachada
            
            escola.save()
            
            solicitacao.status = 'aprovado'
            solicitacao.validado_por = request.user.greuser
            solicitacao.data_validacao = timezone.now()
            messages.success(request, f"A atualização para a escola {escola.nome} foi APROVADA.")

            try:
                AvisoImportante.objects.create(
                    titulo="Dados Cadastrais Atualizados",
                    mensagem=f"Sua solicitação de atualização de dados foi aprovada em {timezone.now().strftime('%d/%m/%Y')}. As novas informações já estão ativas no sistema.",
                    prioridade='normal',
                    criado_por=request.user.greuser,
                    escola=escola,
                    ativo=True,
                    data_expiracao=timezone.now() + timedelta(days=14)
                )
            except Exception as e:
                messages.error(request, f"Aviso de aprovação não pôde ser criado. Erro: {e}")

        # Se o botão 'recusar' foi clicado
        elif 'recusar' in request.POST:
            justificativa = request.POST.get('observacao', 'Nenhuma justificativa foi fornecida.')
            
            solicitacao.status = 'recusado'
            solicitacao.observacao_validacao = justificativa # Salva a justificativa
            solicitacao.validado_por = request.user.greuser
            solicitacao.data_validacao = timezone.now()
            messages.warning(request, f"A atualização para a escola {escola.nome} foi RECUSADA.")

            # =================================================================
            # NOVO: CRIAR AVISO AUTOMÁTICO DE RECUSA
            # =================================================================
            try:
                AvisoImportante.objects.create(
                    titulo="Solicitação de Atualização Recusada",
                    # A mensagem do aviso agora inclui a justificativa
                    mensagem=f"Sua solicitação de atualização foi recusada. Motivo: '{justificativa} '. Por favor, verifique os dados e envie uma nova solicitação.",
                    prioridade='alta', # Prioridade alta para chamar atenção
                    criado_por=request.user.greuser,
                    escola=escola,
                    ativo=True,
                    data_expiracao=timezone.now() + timedelta(days=14)
                )
            except Exception as e:
                messages.error(request, f"Aviso de recusa não pôde ser criado. Erro: {e}")
            # =================================================================
        
        solicitacao.save()
        return redirect('lista_validacoes_pendentes')