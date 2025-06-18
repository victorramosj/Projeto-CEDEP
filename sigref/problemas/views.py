
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
from .models import (AvisoImportante, ConfirmacaoAviso, Lacuna,ProblemaUsuario, STATUS_CHOICES)
from .serializers import (AvisoImportanteSerializer, LacunaSerializer,ProblemaUsuarioSerializer)


# =============================================================================
#  VIEW DA DASHBOARD
# =============================================================================
class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser

        # Inicializar a variável escola
        escola = None

        # Se o usuário for do tipo 'escola', redireciona para sua própria escola
        if gre_user.is_escola():
            escola = gre_user.escolas.first()
            context['escola'] = escola

        # Caso contrário, tenta buscar a escola pelo ID passado na URL
        else:
            escola_id = self.kwargs.get('escola_id')
            if escola_id:
                escola = get_object_or_404(Escola, id=escola_id)
                context['escola'] = escola

        # Verifique se a variável escola foi atribuída corretamente
        if escola is None:
            context['error_message'] = "Escola não encontrada ou não associada ao usuário."
        else:

            # ::AVISOS:: Buscar avisos válidos da escola
            avisos = AvisoImportante.objects.filter(
                escola=escola,
                ativo=True
            ).filter(
                Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
            ).order_by('-prioridade', '-data_criacao')
            
            agora = timezone.now()

            # Estatísticas de lacunas
            todas_lacunas = Lacuna.objects.all()
            lacunas_total = todas_lacunas.count()

            total_lacunas = Lacuna.objects.filter(escola=escola).count() # Contagem de lacunas para a escola
            lacunas_resolvidas = Lacuna.objects.filter(escola= escola, status='R').count()
            lacunas_pendentes = Lacuna.objects.filter(escola= escola,status='P').count()
            lacunas_andamento = Lacuna.objects.filter(escola= escola,status='E').count()
            # Contagem de problemas criados neste mês
            lacunas_este_mes = Lacuna.objects.filter(escola= escola,criado_em__month=agora.month, criado_em__year=agora.year).count()
            
            # Estatísticas de problemas
            total_problemas = ProblemaUsuario.objects.filter(escola=escola).count() # Contagem de problemas dos usuários associados à escola9
            problemas = ProblemaUsuario.objects.filter(escola=escola)
            # Contagem de problemas criados neste mês
            problemas_este_mes = problemas.filter(criado_em__month=agora.month, criado_em__year=agora.year).count()
            # Contagem por status de problemas
            problemas_resolvidos = problemas.filter(status='R').count()
            problemas_pendentes = problemas.filter(status='P').count()
            problemas_andamento = problemas.filter(status='E').count()

            # Contexto enviado ao template
            context.update({
                'gre_user': gre_user,
                'escola': escola,
                'avisos': avisos,
                'setor': Setor.objects.all(),
                'form_problema': ProblemaUsuarioForm(),
                'form_lacuna': LacunaForm(),
                'todas_lacunas': todas_lacunas,
                'lacunas_total': lacunas_total, 	# Total de lacunas geral

                #CONTEXTO DE LACUNAS ESPECIFICO POR ESCOLA
                'total_lacunas': total_lacunas, # Total de lacuna especifico por escola
                'lacunas_resolvidas': lacunas_resolvidas,
                'lacunas_pendentes': lacunas_pendentes,
                'lacunas_andamento': lacunas_andamento,
                'lacunas_este_mes': lacunas_este_mes,

                #CONTEXTO DE PROBLEMAS ESPECIFICO POR ESCOLA
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
    paginator = Paginator(lacunas_list, 9)
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

    # Paginação
    paginator = Paginator(problemas_list, 9) 	# 9 itens por página
    page_number = request.GET.get('page')
    problemas_page = paginator.get_page(page_number)
    total_problemas = problemas_list.count() 	# Total de problemas filtrados

    # Passar os dados para o template
    context = {
        'problemas_page': problemas_page,
        'total_problemas': total_problemas, 	# Total de problemas filtrados
        'search_query': escola_query, 	# Termo de busca (para manter na barra de pesquisa)
        'request': request, # Passa o request para o template
        'status_choices': STATUS_CHOICES, #Passa as opções para o template
    }

    return render(request, 'tela_problemas.html', context)


# =============================================================================
#  VIEWS DE AVISOS
# =============================================================================
@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser

    if gre_user.is_admin():
        avisos_queryset = AvisoImportante.objects.all()
    else:
        avisos_queryset = AvisoImportante.objects.filter(criado_por=gre_user)

    prioridade_filtro = request.GET.get('prioridade', None)

    if prioridade_filtro and prioridade_filtro in ['alta', 'normal', 'baixa']:
        avisos_queryset = avisos_queryset.filter(prioridade=prioridade_filtro)
    avisos_ordenados = avisos_queryset.order_by('-data_criacao')

    paginator = Paginator(avisos_ordenados, 9) 	
    page_number = request.GET.get('page')
    avisos_paginated = paginator.get_page(page_number)

    context = {
        'avisos': avisos_paginated,
        'prioridade_atual': prioridade_filtro,
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
    
    # Verificação de permissão para garantir que o usuário possa editar o aviso
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        messages.error(request, "Você não tem permissão para editar este aviso.")
        return redirect('listar_avisos')

    # Se for um POST, tentamos editar o aviso
    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            messages.success(request, "Aviso editado com sucesso!")
            return redirect('listar_avisos') 	# Redireciona após salvar
        else:
            messages.error(request, "Houve um erro ao editar o aviso.")
            return render(request, 'avisos/editar_aviso.html', {'form': form, 'aviso': aviso})
    
    # Se for um GET, mostramos o formulário de edição
    form = AvisoForm(instance=aviso)
    return render(request, 'problemas/listar_avisos.html', {'form': form, 'aviso': aviso})

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
@login_required
def confirmar_visualizacao_aviso(request, aviso_id):
    # Recupera o aviso com o ID fornecido
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)

    # Cria ou atualiza a confirmação do aviso
    confirmacao, created = ConfirmacaoAviso.objects.get_or_create(
        aviso=aviso,
        escola=request.user.greuser.escolas.first() 	# Associando a escola do usuário
    )

    # Caso ainda não tenha sido visualizado, muda o status
    if confirmacao.status == 'pendente':
        confirmacao.confirmar_visualizado()
    return redirect('listar_avisos') 	# Redireciona para a página de avisos ou a página desejada
