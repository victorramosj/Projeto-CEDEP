from rest_framework import viewsets, permissions
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


# DASHBOARD DA ESCOLA
class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser
        escola = gre_user.escolas.first()

        # Buscar avisos válidos da escola
        avisos = AvisoImportante.objects.filter(
            escola=escola,
            ativo=True
        ).filter(
            Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
        ).order_by('-prioridade', '-data_criacao')

        # Estatísticas
        total_lacunas = Lacuna.objects.filter(escola=escola).count()
        total_problemas = ProblemaUsuario.objects.filter(usuario=gre_user).count()

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


# VIEW PARA EDITAR AVISO
def editar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)

    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            return redirect('listar_avisos')  # Ajuste para sua view de listagem
    else:
        form = AvisoForm(instance=aviso)

    return render(request, 'problemas/editar_aviso.html', {'form': form})


# LISTAR AVISOS
@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser
    if gre_user.is_escola():
        avisos = AvisoImportante.objects.filter(escola=gre_user.escolas.first(), ativo=True)
    else:
        avisos = AvisoImportante.objects.filter(criado_por=gre_user, ativo=True)

    escolas = Escola.objects.all()
    return render(request, 'problemas/listar_avisos.html', {
        'avisos': avisos,
        'gre_user': gre_user,
        'escolas': escolas,
    })


from django.contrib import messages

@login_required
def criar_aviso_view(request):
    gre_user = request.user.greuser
    if gre_user.is_escola():
        return redirect('listar_avisos')

    escolas = Escola.objects.all()

    busca = request.GET.get('busca')
    if busca:
        palavras_chave = busca.split()
        query = Q()
        for palavra in palavras_chave:
            query |= Q(nome__icontains=palavra)
        escolas = escolas.filter(query)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        prioridade = request.POST.get('prioridade', 'normal')
        data_expiracao = request.POST.get('data_expiracao')
        
        escolas_ids = request.POST.getlist('escola_id')

        if 'todas' in escolas_ids:
            escolas_destino = escolas
        else:
            escolas_destino = Escola.objects.filter(id__in=escolas_ids)

        for escola in escolas_destino:
            AvisoImportante.objects.create(
                titulo=titulo,
                mensagem=mensagem,
                prioridade=prioridade,
                escola=escola,
                criado_por=gre_user,
                ativo=True,
                data_expiracao=data_expiracao if data_expiracao else None
            )
        
        messages.success(request, "Aviso publicado com sucesso!")  # mensagem de sucesso
        return redirect('listar_avisos')

    return render(request, 'avisos/criar_aviso.html', {'escolas': escolas})




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
from .models import AvisoImportante
from django.urls import reverse

def apagar_aviso_view(request, aviso_id):
    aviso = get_object_or_404(AvisoImportante, id=aviso_id)
    if request.method == 'POST':
        aviso_titulo = aviso.titulo  # Para usar na mensagem de sucesso
        aviso.delete()
        messages.success(request, f"O aviso '{aviso_titulo}' foi apagado com sucesso!")

        # Redireciona para a página de listagem de avisos
        return redirect(reverse('listar_avisos'))  # Sem namespace, apenas o nome da URL

    # Se o método não for POST, redirecione para a lista de avisos também,
    # pois não se deve apagar com GET.
    return redirect(reverse('listar_avisos'))  # Redirecionamento padrão

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

