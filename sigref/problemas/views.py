from rest_framework import viewsets, permissions
from .models import Lacuna, ProblemaUsuario
from .serializers import LacunaSerializer, ProblemaUsuarioSerializer
from .forms import ProblemaUsuarioForm
from django.shortcuts import render, redirect


from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from monitoramento.models import GREUser, Escola  # ajuste o import conforme sua estrutura

class EscolaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escolas/escola_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gre_user = self.request.user.greuser  # Supondo que todo usuário tenha um GREUser associado
        escola = gre_user.escolas.first()  # Assumindo que GREUser está relacionado a uma ou mais escolas

        context['gre_user'] = gre_user
        context['escola'] = escola
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
