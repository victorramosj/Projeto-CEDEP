from rest_framework import viewsets, permissions
from .models import Lacuna, ProblemaUsuario, AvisoImportante
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm, LacunaForm # importe seu formulário

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from monitoramento.models import GREUser, Escola, Setor

from .models import Lacuna, ProblemaUsuario, AvisoImportante
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm, LacunaForm, AvisoForm

# View da DASHBOARD
class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser

        # Se o usuário for do tipo 'escola', redireciona para sua própria escola
        if gre_user.is_escola():
            escola = gre_user.escolas.first() # Obtém a primeira escola associada ao usuário
            context['escola'] = escola # Exibe o perfil da escola associada ao usuário

        else:
            escola_id = self.kwargs.get('escola_id')
            if escola_id:
                escola = get_object_or_404(Escola, id=escola_id)  # Busca a escola com o ID
                context['escola'] = escola

        # Buscar avisos válidos da escola
        avisos = AvisoImportante.objects.filter(
            escola=escola,
            ativo=True
        ).filter(
            Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
        ).order_by('-prioridade', '-data_criacao')

        # Estatísticas
        total_lacunas = Lacuna.objects.filter(escola=escola).count() # Contagem de lacunas para a escola
        usuarios_da_escola = escola.usuarios.all()
        total_problemas = ProblemaUsuario.objects.filter(usuario__in=usuarios_da_escola).count() # Contagem de problemas dos usuários associados à escola
        
        # Contexto enviado ao template
        context.update({
            'gre_user': gre_user,
            'escola': escola,
            'avisos': avisos,
            'setor': Setor.objects.all(),
            'form_problema': ProblemaUsuarioForm(),
            'form_lacuna': LacunaForm(),
            'total_lacunas': total_lacunas,
            'total_problemas': total_problemas,
        })
        return context


# VIEWSETS PARA API REST
class LacunaViewSet(viewsets.ModelViewSet):
    serializer_class = LacunaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        if user.is_admin() or user.is_coordenador():
            return Lacuna.objects.all()
        return Lacuna.objects.filter(escola__in=user.escolas.all())


class ProblemaUsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemaUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        if user.is_admin() or user.is_coordenador():
            return ProblemaUsuario.objects.all()
        if user.is_chefe_setor():
            return ProblemaUsuario.objects.filter(setor=user.setor)
        return ProblemaUsuario.objects.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user.greuser)


# sigref/problemas/views.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from .forms import AvisoForm
from .models import AvisoImportante

# RELATAR LACUNA
def relatar_lacuna_view(request):
    if request.method == 'POST':
        form = LacunaForm(request.POST)
        if form.is_valid():
            lacuna = form.save(commit=False)
            lacuna.escola = request.user.greuser.escolas.first()
            lacuna.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# RELATAR PROBLEMA
def relatar_problema_view(request):
    if request.method == 'POST':
        form = ProblemaUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            problema = form.save(commit=False)
            problema.usuario = request.user.greuser
            problema.save()
            return redirect('escola_dashboard')
    else:
        form = ProblemaUsuarioForm()
    return render(request, 'escolas/relatar_problema.html', {'form': form})


def problema_dashboard_view(request):
    form = ProblemaUsuarioForm()
    return render(request, 'escolas/escola_dashboard.html', {'form': form})  # type: ignore

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import AvisoImportante

@login_required
def apagar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser

    # Verifica se o aviso foi criado pelo usuário ou se ele é administrador
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        return HttpResponseForbidden("Você não tem permissão para apagar este aviso.")

    if request.method == 'POST':
        aviso.delete()
        messages.success(request, "Aviso apagado com sucesso!")
        return redirect('listar_avisos')  # Redireciona para a página de listagem de avisos

    # Se não for POST, retorna à lista de avisos
    return redirect('listar_avisos')



from django.shortcuts import render
from .models import Escola

def listar_escolas(request):
    query = request.GET.get('q', '')  # pegar o termo da pesquisa

    # filtrar pelo nome, inep, email, nome_gestor, etc (exemplo básico com OR)
    if query:
        escolas = Escola.objects.filter(
            Q(nome__icontains=query) |
            Q(inep__icontains=query) |
            Q(email_escola__icontains=query) |
            Q(nome_gestor__icontains=query) |
            Q(telefone_gestor__icontains=query) |
            Q(email_gestor__icontains=query) |
            Q(endereco__icontains=query)
        )
    else:
        escolas = Escola.objects.all()

    return render(request, 'escolas/lista.html', {
        'escolas': escolas,
        'query': query,
    })

# sigref/problemas/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden
from .models import AvisoImportante

@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser

    # Administradores podem ver todos os avisos
    if gre_user.is_admin():
        avisos = AvisoImportante.objects.all()
    else:
        # Outros usuários podem ver apenas os avisos que eles mesmos criaram
        avisos = AvisoImportante.objects.filter(criado_por=gre_user)

    return render(request, 'problemas/listar_avisos.html', {'avisos': avisos})

# sigref/problemas/views.py

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



# sigref/problemas/views.py

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import AvisoImportante
from .forms import AvisoForm

@login_required
def editar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    gre_user = request.user.greuser

    # Verifica se o aviso foi criado pelo usuário ou se ele é administrador
    if aviso.criado_por != gre_user and not gre_user.is_admin():
        return HttpResponseForbidden("Você não tem permissão para editar este aviso.")

    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            messages.success(request, "Aviso editado com sucesso!")
            return redirect('listar_avisos')  # Redireciona para a página de listagem de avisos
    else:
        form = AvisoForm(instance=aviso)

    return render(request, 'problemas/editar_aviso.html', {'form': form})
