from rest_framework import viewsets, permissions
from .models import Lacuna, ProblemaUsuario
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm
from django.shortcuts import render, redirect

from .models import AvisoImportante
from django.utils import timezone
from django.db.models import Q



from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from monitoramento.models import GREUser, Escola  # ajuste o import conforme sua estrutura

from .models import AvisoImportante  # Adicione no topo do arquivo
from django.utils import timezone
from django.db.models import Q

class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser
        escola = gre_user.escolas.first()

        # 🔥 Buscar avisos válidos da escola
        avisos = AvisoImportante.objects.filter(
            escola=escola,
            ativo=True
        ).filter(
            Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
        ).order_by('-prioridade', '-data_criacao')

        context['gre_user'] = gre_user
        context['escola'] = escola
        context['avisos'] = avisos  # 👈 essa linha envia os avisos pro template
        return context



class LacunaViewSet(viewsets.ModelViewSet):
    serializer_class = LacunaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        if user.is_admin() or user.is_coordenador():
            return Lacuna.objects.all()
        # Monitores e escolas veem apenas suas escolas
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
        # Usuário padrão vê apenas seus próprios relatos
        return ProblemaUsuario.objects.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user.greuser)

def problema_dashboard_view(request):
    return render(request, 'escolas/escola_dashboard.html', {'form': form}) # type: ignore

def relatar_problema_view(request):
    if request.method == 'POST':
        form = ProblemaUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            problema = form.save(commit=False)
            problema.usuario = request.user.greuser  # associa ao usuário logado
            problema.save()
            return redirect('dashboard')  # redireciona após salvar
    else:
        form = ProblemaUsuarioForm()
    return render(request, 'escolas/relatar_problema.html', {'form': form})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import AvisoImportante
from monitoramento.models import Escola

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from monitoramento.models import Escola
from .models import AvisoImportante

@login_required
def listar_avisos_view(request):
    gre_user = request.user.greuser
    if gre_user.is_escola():
        avisos = AvisoImportante.objects.filter(escola=gre_user.escolas.first(), ativo=True)
    else:
        avisos = AvisoImportante.objects.filter(criado_por=gre_user, ativo=True)

    escolas = Escola.objects.all()  # Para popular select no modal
    return render(request, 'problemas/listar_avisos.html', {
        'avisos': avisos,
        'gre_user': gre_user,
        'escolas': escolas,
    })

@login_required
def criar_aviso_view(request):
    gre_user = request.user.greuser
    if gre_user.is_escola():
        return redirect('listar_avisos')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        escola_id = request.POST.get('escola_id')
        prioridade = request.POST.get('prioridade', 'normal')

        aviso = AvisoImportante.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            prioridade=prioridade,
            escola=Escola.objects.get(id=escola_id),
            criado_por=gre_user,
            ativo=True
        )
        return redirect('listar_avisos')

    return redirect('listar_avisos')  # Se chegar via GET, só redireciona

