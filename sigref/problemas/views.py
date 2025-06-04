from rest_framework import viewsets, permissions
from .models import Lacuna, ProblemaUsuario, AvisoImportante
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm, LacunaForm # importe seu formulário

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils import timezone

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from monitoramento.models import GREUser, Escola, Setor  # ajuste o import conforme sua estrutura


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

            # Estatísticas
            total_lacunas = Lacuna.objects.filter(escola=escola).count() # Contagem de lacunas para a escola
            usuarios_da_escola = escola.usuarios.all()
            total_problemas = ProblemaUsuario.objects.filter(usuario__in=usuarios_da_escola).count() # Contagem de problemas dos usuários associados à escola
            
            problemas = ProblemaUsuario.objects.filter(usuario__in=usuarios_da_escola)
            # Contagem de problemas criados neste mês
            agora = timezone.now()
            problemas_este_mes = problemas.filter(criado_em__month=agora.month, criado_em__year=agora.year).count()
                
                 # Contagem por status
            problemas_resolvidos = problemas.filter(status='resolvido').count()
            problemas_pendentes = problemas.filter(status='pendente').count()
            problemas_andamento = problemas.filter(status='andamento').count()
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
                'problemas_resolvidos': problemas_resolvidos,
                'problemas_pendentes': problemas_pendentes,
                'problemas_andamento': problemas_andamento,
                'problemas_este_mes': problemas_este_mes,
            })

        return context


# View das LACUNAS
class LacunaViewSet(viewsets.ModelViewSet):
    serializer_class = LacunaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.greuser
        if user.is_admin() or user.is_coordenador():
            return Lacuna.objects.all()
        # Monitores e escolas veem apenas suas escolas
        return Lacuna.objects.filter(escola__in=user.escolas.all())

# View dos PROBLEMAS
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
    form = ProblemaUsuarioForm()
    return render(request, 'escolas/escola_dashboard.html', {'form': form}) # type: ignore

def relatar_problema_view(request):
    if request.method == 'POST':
        form = ProblemaUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            problema = form.save(commit=False)
            problema.usuario = request.user.greuser
            problema.save()
            return redirect('escola_dashboard')  # redireciona após salvar
    else:
        form = ProblemaUsuarioForm()
    return render(request, 'escolas/relatar_problema.html', {'form': form})


from django.contrib.auth.decorators import login_required

# View de AVISOS IMPORTANTES
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


def relatar_lacuna_view(request):    
    if request.method == 'POST':
        form = LacunaForm(request.POST)
        lacuna = form.save(commit=False)
        lacuna.escola = request.user.greuser.escolas.first()
        lacuna.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
            # opcional: aqui você poderia salvar os erros em messages framework
        pass       
    # volta para a página de onde veio (dashboard) 
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    