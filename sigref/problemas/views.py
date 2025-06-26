
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

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

# -----------------------------------------------------------------------------
# Imports da aplicação local
# -----------------------------------------------------------------------------
from monitoramento.models import Escola, GREUser, Setor

from .forms import AvisoForm, LacunaForm, ProblemaUsuarioForm
from .models import (AvisoImportante, ConfirmacaoAviso, Lacuna, ProblemaUsuario, STATUS_CHOICES)
from .serializers import (AvisoImportanteSerializer, LacunaSerializer, ProblemaUsuarioSerializer)

# ADICIONADO DEPOIS 
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import AvisoImportante, ConfirmacaoAviso, GREUser # Importe GREUser

# =============================================================================
#  VIEW DA DASHBOARD
# =============================================================================

class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    # O nome do template que esta view irá renderizar.
    # O seu pode ser 'escola_dashboard.html' ou 'cedepe/escola_dashboard.html', ajuste se necessário.
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser

        # Inicializar a variável escola
        escola = None

        # Se o usuário for do tipo 'escola', usa a sua própria escola
        if gre_user.is_escola():
            escola = gre_user.escolas.first()
            context['escola'] = escola
        # Caso contrário, busca a escola pelo ID passado na URL (para admins, etc.)
        else:
            escola_id = self.kwargs.get('escola_id')
            if escola_id:
                escola = get_object_or_404(Escola, id=escola_id)
                context['escola'] = escola

        # Verifique se a variável escola foi atribuída corretamente antes de prosseguir
        if escola is None:
            context['error_message'] = "Escola não encontrada ou não associada ao usuário."
        else:
            # =================================================================
            # LÓGICA DE AVISOS - INÍCIO DA CORREÇÃO
            # =================================================================

            # 1. Pega todos os avisos válidos para a escola (seu código original, que está correto)
            avisos_queryset = AvisoImportante.objects.filter(
                escola=escola,
                ativo=True
            ).filter(
                Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
            ).order_by('-prioridade', '-data_criacao')

            # 2. Busca os IDs de todos os avisos que ESTA escola já marcou como 'visualizado'
            # Usamos set() para uma verificação de 'in' muito mais rápida.
            avisos_visualizados_ids = set(ConfirmacaoAviso.objects.filter(
                escola=escola,
                status='visualizado'
            ).values_list('aviso_id', flat=True))

            # 3. Percorre a lista de avisos e adiciona um novo atributo "ja_visualizado"
            # Este atributo será True ou False e poderá ser usado diretamente no template
            for aviso in avisos_queryset:
                aviso.ja_visualizado = aviso.id in avisos_visualizados_ids
            
            # AGORA, a variável 'avisos_queryset' contém a informação de visualização.
            
            # =================================================================
            # LÓGICA DE AVISOS - FIM DA CORREÇÃO
            # =================================================================

            agora = timezone.now()

            # O restante do seu código para estatísticas permanece exatamente igual
            # Estatísticas de lacunas
            todas_lacunas = Lacuna.objects.all()
            lacunas_total = todas_lacunas.count()
            total_lacunas = Lacuna.objects.filter(escola=escola).count()
            lacunas_resolvidas = Lacuna.objects.filter(escola=escola, status='R').count()
            lacunas_pendentes = Lacuna.objects.filter(escola=escola, status='P').count()
            lacunas_andamento = Lacuna.objects.filter(escola=escola, status='E').count()
            lacunas_este_mes = Lacuna.objects.filter(escola=escola, criado_em__month=agora.month, criado_em__year=agora.year).count()
            
            # Estatísticas de problemas
            total_problemas = ProblemaUsuario.objects.filter(escola=escola).count()
            problemas = ProblemaUsuario.objects.filter(escola=escola)
            problemas_este_mes = problemas.filter(criado_em__month=agora.month, criado_em__year=agora.year).count()
            problemas_resolvidos = problemas.filter(status='R').count()
            problemas_pendentes = problemas.filter(status='P').count()
            problemas_andamento = problemas.filter(status='E').count()

            # Contexto final enviado ao template
            context.update({
                'gre_user': gre_user,
                'escola': escola,
                'avisos': avisos_queryset,  # Passa a lista de avisos JÁ MODIFICADA
                'setor': Setor.objects.all(),
                'form_problema': ProblemaUsuarioForm(),
                'form_lacuna': LacunaForm(),
                'todas_lacunas': todas_lacunas,
                'lacunas_total': lacunas_total,

                # CONTEXTO DE LACUNAS ESPECIFICO POR ESCOLA
                'total_lacunas': total_lacunas,
                'lacunas_resolvidas': lacunas_resolvidas,
                'lacunas_pendentes': lacunas_pendentes,
                'lacunas_andamento': lacunas_andamento,
                'lacunas_este_mes': lacunas_este_mes,

                # CONTEXTO DE PROBLEMAS ESPECIFICO POR ESCOLA
                'total_problemas': total_problemas,
                'problemas_resolvidos': problemas_resolvidos,
                'problemas_pendentes': problemas_pendentes,
                'problemas_andamento': problemas_andamento,
                'problemas_este_mes': problemas_este_mes,
            })

        return context


# =============================================================================
#  VIEW DA ATUALIZAÇÃO DE STATUS DA LACUNA
# =============================================================================
class UpdateStatusLacuna(APIView):
    def post(self, request, lacuna_id):
        lacuna = get_object_or_404(Lacuna, id=lacuna_id)
        new_status = request.data.get('status')

        if new_status in ['P', 'R', 'E']: 	# Validar o status
            lacuna.status = new_status
            lacuna.save()
            return Response(LacunaSerializer(lacuna).data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Status inválido"}, status=status.HTTP_400_BAD_REQUEST)


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
class UpdateStatusProblema(APIView):
    def post(self, request, problema_id):
        problema = get_object_or_404(ProblemaUsuario, id=problema_id)
        new_status = request.data.get('status')

        if new_status in ['P', 'R', 'E']: 	# Validar o status
            problema.status = new_status
            problema.save()
            return Response(ProblemaUsuarioSerializer(problema).data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Status inválido"}, status=status.HTTP_400_BAD_REQUEST)

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
def tela_lacuna_view(request):
    lacunas_list = Lacuna.objects.select_related('escola').all()
    
    # Pega os parâmetros da URL, exatamente como antes.
    search_query = request.GET.get('q', '')
    data_filter = request.GET.get('data', '')
    status_filter = request.GET.get('status', '')
    # Filtro por Escola
    if search_query:
        lacunas_list = lacunas_list.filter(escola__nome__icontains=search_query)

    # Filtro por Data
    if data_filter == '1': 	# Última semana
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(weeks=1))
    elif data_filter == '2': 	# Último mês
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(days=30))
    elif data_filter == '3': 	# Último ano
        lacunas_list = lacunas_list.filter(criado_em__gte=datetime.now() - timedelta(days=365))

    #  Filtro por Status
    if status_filter:
        lacunas_list = lacunas_list.filter(status=status_filter)

    lacunas_list = lacunas_list.order_by('-criado_em')
    
    # Paginação, como antes.
    paginator = Paginator(lacunas_list, 8)
    page_number = request.GET.get('page')
    lacunas_page = paginator.get_page(page_number)

    # Prepara o contexto para o template.
    context = {
        'lacunas_page': lacunas_page,
        'todas_lacunas': paginator.count, # Usar paginator.count é mais eficiente aqui.
        'search_query': search_query,
        'data_filter': data_filter,
        'status_filter': status_filter,
        'request': request,
        'status_choices': STATUS_CHOICES,
    }

    # A view agora SEMPRE renderiza o template completo. Sem ifs.
    return render(request, 'tela_lacunas.html', context)


# =============================================================================
#  VIEW DA TELA PROBLEMA
# =============================================================================
def tela_problema_view(request):
    problemas_list = ProblemaUsuario.objects.select_related('escola', 'usuario__user', 'setor').all()

    # Obter os parâmetros de filtro da URL (busca por escola, data e status)
    escola_query = request.GET.get('escola', '') 	# Pesquisa pela escola
    data_filter = request.GET.get('data', '')
    status_filter = request.GET.get('status', '')
    setor_filter = request.GET.get('setor', '')

    # Filtro por Escola
    if escola_query:
        problemas_list = problemas_list.filter(escola__nome__icontains=escola_query)

    # Filtro por Data
    if data_filter == '1': 	# Última semana
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(weeks=1))
    elif data_filter == '2': 	# Último mês
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(days=30))
    elif data_filter == '3': 	# Último ano
        problemas_list = problemas_list.filter(criado_em__gte=datetime.now() - timedelta(days=365))

    #  Filtro por Status
    if status_filter:
        problemas_list = problemas_list.filter(status=status_filter)

    # Filtro por Setor
    if setor_filter:
        problemas_list = problemas_list.filter(setor__id=setor_filter)

    todos_os_setores = Setor.objects.all().order_by('nome')

    # Paginação
    paginator = Paginator(problemas_list, 6) 	# 6 itens por página
    page_number = request.GET.get('page')
    problemas_page = paginator.get_page(page_number)
    total_problemas = problemas_list.count() 	# Total de problemas filtrados

    # Passar os dados para o template
    context = {
        'problemas': problemas_page,
        'total_problemas': total_problemas, 	# Total de problemas filtrados
        'search_query': escola_query, 	# Termo de busca (para manter na barra de pesquisa)
        'request': request, # Passa o request para o template
        'status_choices': STATUS_CHOICES, #Passa as opções para o template
        'todos_os_setores': todos_os_setores,
    }

    return render(request, 'tela_problemas.html', context)


# =============================================================================
#  VIEWS DE AVISOS
# =============================================================================
# Em seu arquivo views.py

@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser

    # --- LÓGICA DE FILTRAGEM INICIAL (DATABASE) ---
    if gre_user.is_admin():
        avisos_queryset = AvisoImportante.objects.select_related('escola', 'criado_por__user').all()
    else:
        avisos_queryset = AvisoImportante.objects.select_related('escola', 'criado_por__user').filter(criado_por=gre_user)

    # 1. NOVO: Recebe os parâmetros de filtro da URL
    prioridade_filtro = request.GET.get('prioridade', '')
    status_filtro = request.GET.get('status', '')
    escola_filtro = request.GET.get('q_escola', '')

    # 2. Aplica filtros que podem ser feitos no banco de dados
    if prioridade_filtro:
        avisos_queryset = avisos_queryset.filter(prioridade=prioridade_filtro)
    if escola_filtro:
        avisos_queryset = avisos_queryset.filter(escola__nome__icontains=escola_filtro)

    avisos_ordenados = list(avisos_queryset.order_by('-data_criacao'))

    # --- LÓGICA DE ANOTAÇÃO DE STATUS (PYTHON) ---
    confirmacoes = ConfirmacaoAviso.objects.filter(
        aviso__in=avisos_ordenados,
        status='visualizado'
    ).values('aviso_id')
    
    avisos_visualizados_ids = {conf['aviso_id'] for conf in confirmacoes}

    for aviso in avisos_ordenados:
        aviso.foi_visualizado = aviso.id in avisos_visualizados_ids

    # 3. NOVO: Aplica o filtro de status que depende da anotação em Python
    if status_filtro:
        if status_filtro == 'visualizado':
            avisos_ordenados = [aviso for aviso in avisos_ordenados if aviso.foi_visualizado]
        elif status_filtro == 'pendente':
            avisos_ordenados = [aviso for aviso in avisos_ordenados if not aviso.foi_visualizado]

    # --- PAGINAÇÃO ---
    paginator = Paginator(avisos_ordenados, 9)
    page_number = request.GET.get('page')
    avisos_paginated = paginator.get_page(page_number)

    # 4. NOVO: Passa os filtros atuais de volta para o template
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
        
        # [NOVO] Obtém o arquivo de imagem do request. Será 'None' se nenhum for enviado.
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

                # [NOVO] Adiciona a imagem ao dicionário SOMENTE se ela foi enviada
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

    # Verificação de permissão (sem alterações)
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        messages.error(request, "Você não tem permissão para editar este aviso.")
        return redirect('listar_avisos')

    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            # 1. Salva as alterações (título, mensagem, etc.) no aviso.
            aviso_editado = form.save()

            # 2. Redefine o status de TODAS as confirmações associadas para 'pendente'.
            #    Esta é a única linha necessária para a nova lógica.
            aviso_editado.confirmacoes.all().update(status='pendente')

            messages.success(request, "Aviso editado com sucesso! O status foi redefinido para 'Pendente' para todas as escolas.")
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
    """
    Verifica avisos que estão ativos mas cuja data de expiração já passou.
    Esta lógica é mais precisa, usando os campos do seu modelo.
    """
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
    """
    Recebe uma lista de IDs de avisos via POST e os apaga.
    Esta função agora opera no modelo AvisoImportante.
    """
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
# Em problemas/views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import AvisoImportante, ConfirmacaoAviso, GREUser # Certifique-se de importar os modelos

@login_required
def confirmar_visualizacao_aviso(request, aviso_id):
    # 1. Garante que a requisição é do tipo POST
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)

    # 2. Bloco de verificação de perfil e permissão
    try:
        gre_user = request.user.greuser
        if not gre_user.is_escola:
            return JsonResponse({'status': 'error', 'message': 'Apenas usuários de escolas podem visualizar avisos.'}, status=403)
        
        escola_do_usuario = gre_user.escolas.first()
        if not escola_do_usuario:
            return JsonResponse({'status': 'error', 'message': 'Usuário não está associado a nenhuma escola.'}, status=400)
            
    except (GREUser.DoesNotExist, AttributeError):
        return JsonResponse({'status': 'error', 'message': 'Perfil de usuário inválido ou não encontrado.'}, status=400)

    # 3. Recupera o aviso ou retorna erro 404
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)

    # 4. Busca ou cria o registro de confirmação.
    #    Esta é a verificação de associação correta e suficiente.
    #    Ele garante que estamos agindo sobre a relação entre ESTE aviso e ESTA escola.
    confirmacao, created = ConfirmacaoAviso.objects.get_or_create(
        aviso=aviso,
        escola=escola_do_usuario
    )

    # 5. Altera o status se estiver pendente
    if confirmacao.status == 'pendente':
        confirmacao.confirmar_visualizado() # Chama o método do seu modelo
        return JsonResponse({'status': 'success', 'message': 'Aviso marcado como visualizado.'})
    
    # 6. Se o status já era 'visualizado', apenas informa
    else:
        return JsonResponse({'status': 'already_viewed', 'message': 'Este aviso já havia sido visualizado.'})

# =============================================================================
#  VIEW DA LISTA DE PROBLEMAS POR ESCOLA 
# =============================================================================
@login_required
def lista_problemas_por_escola(request, escola_id):
    """
    Exibe uma lista paginada e filtrável de problemas para uma escola específica,
    respeitando as permissões do usuário logado.
    """
    escola = get_object_or_404(Escola, pk=escola_id)

    # 1. VERIFICAÇÃO DE PERMISSÃO (LÓGICA ESSENCIAL)
    # Garante que o usuário só pode ver dados de escolas que lhe são permitidas.
    if not request.user.greuser.pode_acessar_escola(escola):
        raise PermissionDenied("Você não tem permissão para acessar os dados desta escola.")

    # 2. LÓGICA DE FILTRAGEM E PESQUISA
    # Pega a lista de todos os problemas apenas daquela escola como base.
    queryset = ProblemaUsuario.objects.filter(escola=escola).order_by('-criado_em')

    # Parametros de filtro da URL
    status_filter = request.GET.get('status', '')
    data_filter = request.GET.get('data', '')
    setor_filter = request.GET.get('setor', '')

    # Filtra por status, se o parâmetro 'status' for passado na URL (ex: ?status=P)
    status_filter = request.GET.get('status')
    if status_filter in ['P', 'R', 'E']: # 'P'endente, 'R'esolvido, 'E'm Andamento
        queryset = queryset.filter(status=status_filter)
    
    # Filtra por termo de pesquisa, se houver
    search_query = request.GET.get('q')
    if search_query:
        # Pesquisa na descrição do problema (ajuste o campo se necessário)
        queryset = queryset.filter(descricao__icontains=search_query)

    # Filtra por data
    if data_filter:
        hoje = timezone.now()
        if data_filter == '1':  # Última semana
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(weeks=1))
        elif data_filter == '2':  # Último mês
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(days=30))
        elif data_filter == '3':  # Último ano
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(days=365))

    # Filtra por setor
    if setor_filter:
        queryset = queryset.filter(setor__id=setor_filter)
    
    todos_os_setores = Setor.objects.all().order_by('nome')

    # 3. LÓGICA DE PAGINAÇÃO
    # Evita que páginas com centenas de problemas fiquem lentas.
    paginator = Paginator(queryset, 10) # Mostra 10 problemas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'escola': escola,
        'problemas': page_obj, # Envia o objeto da página para o template, não a lista inteira
        'total_problemas': paginator.count, # Total de problemas após os filtros
        'status_choices': STATUS_CHOICES, # Para popular o dropdown de status
        'request': request, # Passar o request é útil para o template
        
        # Manter o estado dos filtros na interface
        'status_filter': status_filter,
        'search_query': search_query,
        'data_filter': data_filter, 
        'setor_filter': setor_filter,

        # Para popular o dropdown de setores
        'todos_os_setores': todos_os_setores,
    }
    
    return render(request, 'tela_problemas.html', context)

# =============================================================================
#  VIEW DA LISTA DE LACUNAS POR ESCOLA 
# =============================================================================
from django.core.exceptions import PermissionDenied
@login_required
def lista_lacunas_por_escola(request, escola_id):
    """
    Exibe uma lista paginada e filtrável de lacunas para uma escola específica,
    respeitando as permissões do usuário logado.
    """
    escola = get_object_or_404(Escola, pk=escola_id)

    # 1. VERIFICAÇÃO DE PERMISSÃO
    if not request.user.greuser.pode_acessar_escola(escola):
        raise PermissionDenied("Você não tem permissão para acessar os dados desta escola.")
    
    # 2. LÓGICA DE FILTRAGEM E PESQUISA
    # Pega a lista de todas as lacunas apenas daquela escola como base.
    queryset = Lacuna.objects.filter(escola=escola).order_by('-criado_em')

    # Parametros de filtro da URL
    status_filter = request.GET.get('status', '')
    data_filter = request.GET.get('data', '')

    # Filtra por status
    if status_filter in ['P', 'R', 'E']:
        queryset = queryset.filter(status=status_filter)
    
    # Filtra por data
    if data_filter: 
        hoje = timezone.now()
        if data_filter == '1':  # Última semana
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(weeks=1))
        elif data_filter == '2':  # Último mês
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(days=30))
        elif data_filter == '3':  # Último ano
            queryset = queryset.filter(criado_em__gte=hoje - timedelta(days=365))

    search_query = request.GET.get('q')
    if search_query:
        # Pesquisa na disciplina da lacuna (ajuste o campo se necessário)
        queryset = queryset.filter(disciplina__icontains=search_query)

    # 3. LÓGICA DE PAGINAÇÃO
    paginator = Paginator(queryset, 10) # 10 lacunas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'escola': escola,
        'lacunas': page_obj,
        'total_lacunas': paginator.count,
        'status_choices': STATUS_CHOICES,
        'request': request,

        # Manter o estado dos filtros na interface
        'status_filter': status_filter,
        'search_query': search_query,
        'data_filter': data_filter,
        
    }
    
    return render(request, 'tela_lacunas.html', context)
