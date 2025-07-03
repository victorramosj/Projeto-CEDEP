from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import LoginForm

from django.shortcuts import render, redirect
from monitoramento.models import GREUser


from django.shortcuts import redirect, render
from monitoramento.models import GREUser
from problemas.models import Lacuna, ProblemaUsuario

# =============================================================================
#  VIEW PARA DA PÁGINA PRINCIPAL (DASHBOARD)
#  Esta view verifica o tipo de usuário logado e exibe alertas de lacunas
# =============================================================================
def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "cedepe/home.html")

    try:
        # Obtendo o usuário logado
        gre_user = request.user.greuser
        
        # Obter o setor do usuário (se for um "Chefe de Setor" ou "Coordenador")
        setor_do_usuario = gre_user.setor # <--- Variável definida aqui
        escolas = gre_user.escolas.all()  # Obtendo as escolas do usuário, caso ele tenha várias

        # Filtrar lacunas para as escolas do usuário
        lacunas_pendentes = Lacuna.objects.filter(escola__in=escolas, status='P')

        # Filtrar problemas para o setor do usuário
        problemas_pendentes = ProblemaUsuario.objects.filter(setor=setor_do_usuario, status='P')

        # Criar alertas para lacunas e problemas pendentes
        alerts = []

        # Se houver lacunas pendentes
        # LINHA 37 ORIGINALMENTE COM ERRO: if setor and setor.nome.strip().upper() in ['CGAF', 'UDP']:
        if setor_do_usuario and setor_do_usuario.nome.strip().upper() in ['CGAF', 'UDP']: # <--- CORRIGIDO AQUI!
            alerts.append({
                'type': 'lacuna',
                'count': lacunas_pendentes.count(),
                'url': 'tela_lacunas',  # URL para a tela de lacunas
                'text': f"Você tem {lacunas_pendentes.count()} lacuna(s) pendente(s)."
            })

        # Se houver problemas pendentes
        if problemas_pendentes.exists():
            alerts.append({
                'type': 'problema',
                'count': problemas_pendentes.count(),
                'url': 'tela_problemas',  # URL para a tela de problemas
                'text': f"Você tem {problemas_pendentes.count()} problema(s) pendente(s)."
            })

        # Verificar se o usuário é da escola e redirecionar para o dashboard da escola
        if gre_user.is_escola():
            return redirect('escola_dashboard')

        # Para qualquer outro tipo de usuário, renderizar a página principal com os alertas
        return render(request, "cedepe/home.html", {"alerts": alerts})

    except GREUser.DoesNotExist:
        return render(request, "cedepe/home.html")





from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm  # Certifique-se de importar corretamente
from monitoramento.models import GREUser  # Importa o modelo de usuário extendido

# =============================================================================
#  VIEW PARA O LOGIN DO USUÁRIO
# =============================================================================
# Esta view lida com o processo de login do usuário, autenticando-o e redirecionando-o para a página apropriada com base no seu tipo de usuário.
def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                try:
                    gre_user = GREUser.objects.get(user=user)

                    # Exemplo: armazenar tipo de usuário na sessão
                    request.session['tipo_usuario'] = gre_user.tipo_usuario
                    request.session['nome_completo'] = gre_user.nome_completo
                    request.session['nivel_acesso'] = gre_user.nivel_acesso

                    messages.success(request, f"Bem-vindo, {gre_user.nome_completo}!")

                    # Redirecionamento inteligente (ajuste conforme sua lógica)
                    if gre_user.is_admin():
                        return redirect('home')
                    elif gre_user.is_coordenador():
                        return redirect('home')
                    elif gre_user.is_chefe_setor():
                        return redirect('home')
                    elif gre_user.is_monitor():
                        return redirect('home')
                    elif gre_user.is_escola():
                        return redirect('escola_dashboard')
                    else:
                        return redirect('home')  # fallback padrão

                except GREUser.DoesNotExist:
                    # Se o usuário estiver autenticado, mas não tiver um GREUser associado
                    messages.warning(request, "Usuário autenticado, mas sem perfil configurado.")
                    return redirect("home")
            else:
                messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = LoginForm()
    
    return render(request, "cedepe/login.html", {"form": form})

# =============================================================================
#  VIEW PARA FAZER LOGOUT DO USUÁRIO
# =============================================================================
def user_logout(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")

# =============================================================================
#  VIEW PARA REGISTRO DE NOVO USUÁRIO
# =============================================================================
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "cedepe/register.html", {"form": form})


# =============================================================================
#  VIEW PARA DA PÁGINA 'SOBRE'
# =============================================================================
def sobre(request):
    """Esta view renderiza a página 'Sobre'"""
    context = {
        'versao': '1.0.0',
        'autores': 'Giselle Souza Novaes de Sá, João Victor, Lucas Vinicius de Souza Bastos e Victor Kauê da Silva Alves', # Lista de autores
    }
    # Renderiza o template 'sobre.html' com o contexto fornecido
    return render(request, 'cedepe/sobre.html', context)


# =============================================================================
#  VIEW PARA DA PÁGINA 'MANUAL'
# =============================================================================
from django.contrib.auth.decorators import login_required
@login_required
def manual_usuario(request):
    # Sua lógica para a página do manual aqui
    return render(request, 'cedepe/manual.html')
