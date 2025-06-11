from rest_framework import viewsets, permissions
from .models import Lacuna, ProblemaUsuario, AvisoImportante
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm, LacunaForm, AvisoForm # importe seu formulário

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.utils import timezone

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from monitoramento.models import GREUser, Escola, Setor


# View da DASHBOARD
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
                'lacunas_total': lacunas_total,  # Total de lacunas geral

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

# Rest de lacuna para Javascript
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class UpdateStatusLacuna(APIView):
    def post(self, request, lacuna_id):
        lacuna = get_object_or_404(Lacuna, id=lacuna_id)
        new_status = request.data.get('status')

        if new_status in ['P', 'R', 'E']:  # Validar o status
            lacuna.status = new_status
            lacuna.save()
            return Response(LacunaSerializer(lacuna).data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Status inválido"}, status=status.HTTP_400_BAD_REQUEST)
        

class UpdateStatusProblema(APIView):
    def post(self, request, problema_id):
        problema = get_object_or_404(ProblemaUsuario, id=problema_id)
        new_status = request.data.get('status')

        if new_status in ['P', 'R', 'E']:  # Validar o status
            problema.status = new_status
            problema.save()
            return Response(ProblemaUsuarioSerializer(problema).data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Status inválido"}, status=status.HTTP_400_BAD_REQUEST)
        

# views.py
from rest_framework import viewsets
from .models import Lacuna, ProblemaUsuario, AvisoImportante
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer, AvisoImportanteSerializer

class LacunaViewSet(viewsets.ModelViewSet):
    queryset = Lacuna.objects.all()
    serializer_class = LacunaSerializer

class ProblemaUsuarioViewSet(viewsets.ModelViewSet):
    queryset = ProblemaUsuario.objects.all()
    serializer_class = ProblemaUsuarioSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}

class AvisoImportanteViewSet(viewsets.ModelViewSet):
    queryset = AvisoImportante.objects.all()
    serializer_class = AvisoImportanteSerializer


# sigref/problemas/views.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from .forms import AvisoForm
from .models import AvisoImportante

# RELATAR LACUNA
def relatar_lacuna_view(request, escola_id):
    escola = get_object_or_404(Escola, id=escola_id)  # Obtém a escola com o ID da URL

    if request.method == 'POST':
        form = LacunaForm(request.POST)
        if form.is_valid():
            lacuna = form.save(commit=False)
            lacuna.escola = escola  # Associa a lacuna à escola
            lacuna.save()
            return redirect('dashboard_escola', escola_id=escola.id)  # Redireciona para o dashboard da escola
    else:
        form = LacunaForm()

    return render(request, 'escolas/relatar_lacuna.html', {'form': form, 'escola': escola})


# RELATAR PROBLEMA
def relatar_problema_view(request, escola_id):
    escola = get_object_or_404(Escola,id= escola_id)


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


def problema_dashboard_view(request):
    form = ProblemaUsuarioForm()
    return render(request, 'escolas/escola_dashboard.html', {'form': form})  # type: ignore

from django.core.paginator import Paginator

# TELA LACUNA CGAF/UDP
def tela_lacuna_view(request):
    # Obtém todas as lacunas da escola
    lacunas_list = Lacuna.objects.all()

    # Cria o objeto paginator para limitar a 9 lacunas por página
    paginator = Paginator(lacunas_list, 9)

    page_number = request.GET.get('page')
    lacunas_page = paginator.get_page(page_number)

    # Passa as lacunas paginadas para o template
    return render(request, 'tela_lacunas.html', {'lacunas_page': lacunas_page})



# TELA PROBLEMA
def tela_problema_view(request):
    # Obtém todas as lacunas da escola
    problemas_list = ProblemaUsuario.objects.all()

    # Cria o objeto paginator para limitar a 9 lacunas por página
    paginator = Paginator(problemas_list, 9)

    page_number = request.GET.get('page')
    problemas_page = paginator.get_page(page_number)

    # Passa as lacunas paginadas para o template
    return render(request, 'tela_problemas.html', {'problemas_page': problemas_page})

# VIEWS AVISOS *********************************************************

@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser

    # Administradores podem ver todos os avisos
    if gre_user.is_admin():
        avisos = AvisoImportante.objects.all()
    else:
        # Outros usuários podem ver apenas os avisos que eles mesmos criaram
        avisos = AvisoImportante.objects.filter(criado_por=gre_user)

    # Aplicando a paginação
    paginator = Paginator(avisos, 9)  # 9 avisos por página
    page_number = request.GET.get('page')  # Número da página atual
    avisos_paginated = paginator.get_page(page_number)  # Obtemos os avisos para a página atual

    return render(request, 'problemas/listar_avisos.html', {'avisos': avisos_paginated})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import AvisoImportante, Escola
from django.contrib.auth.decorators import login_required

@login_required
def criar_aviso_view(request):
    gre_user = request.user.greuser

    # Verifica se o usuário é do tipo 'Escola' e bloqueia o acesso
    if gre_user.is_escola():
        messages.error(request, "Usuários do tipo 'Escola' não têm permissão para criar avisos.")
        return redirect('listar_avisos')  # Redireciona para a página de avisos

    escolas = Escola.objects.all()  # Pega todas as escolas disponíveis para selecionar

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        prioridade = request.POST.get('prioridade', 'normal')
        data_expiracao = request.POST.get('data_expiracao')
        escolas_ids = request.POST.getlist('escola_id')  # Obtém as escolas selecionadas

        # Validação simples para garantir que o título e a mensagem não estão vazios
        if not titulo or not mensagem:
            messages.error(request, "O título e a mensagem são obrigatórios.")
            return render(request, 'avisos/criar_aviso.html', {'escolas': escolas})

        if not escolas_ids:  # Verifica se ao menos uma escola foi selecionada
            messages.error(request, "Pelo menos uma escola precisa ser selecionada.")
            return render(request, 'avisos/criar_aviso.html', {'escolas': escolas})

        # Criando o aviso
        for escola_id in escolas_ids:
            escola = Escola.objects.get(id=escola_id)  # Obtém a escola correspondente ao ID
            AvisoImportante.objects.create(
                titulo=titulo,
                mensagem=mensagem,
                prioridade=prioridade,
                criado_por=gre_user,
                escola=escola,  # Associando o aviso à escola
                ativo=True,
                data_expiracao=data_expiracao if data_expiracao else None
            )

        messages.success(request, "Aviso criado com sucesso!")
        return redirect('listar_avisos')  # Redireciona para a página de avisos

    # Quando for GET, passa as escolas para o template
    return render(request, 'avisos/criar_aviso.html', {'escolas': escolas})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AvisoImportante
from .forms import AvisoForm

# views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AvisoImportante
from .forms import AvisoForm

from django.http import JsonResponse

@login_required
def editar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser
    
    # Verificação de permissão
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        return JsonResponse({
            'errors': ['Você não tem permissão para editar este aviso.']
        }, status=403)

    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': 'Aviso editado com sucesso!'})
        else:
            errors = []
            for field, error_list in form.errors.items():
                for error in error_list:
                    errors.append(f"{field}: {error}")
            return JsonResponse({'errors': errors}, status=400)
    
    return JsonResponse({
        'errors': ['Método não permitido']
    }, status=405)



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AvisoImportante

@login_required
def apagar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser

    # Verifica se o aviso foi criado pelo usuário ou se ele é administrador
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        messages.error(request, "Você não tem permissão para excluir este aviso.")
        return redirect('listar_avisos')  # Redireciona para a página de avisos

    aviso.delete()
    messages.success(request, "Aviso excluído com sucesso!")
    return redirect('listar_avisos')  # Redireciona para a lista de avisos após a exclusão

