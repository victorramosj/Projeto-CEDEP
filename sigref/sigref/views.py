from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import LoginForm

from django.shortcuts import render, redirect
from monitoramento.models import GREUser


from django.shortcuts import redirect, render
from monitoramento.models import GREUser 

def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "cedepe/home.html")

    try:
        gre_user = GREUser.objects.get(user=request.user)

        if gre_user.is_escola():
            return redirect('escola_dashboard')  # 🔁 redireciona para a view específica

        # 👇 para qualquer outro tipo de usuário
        return render(request, "cedepe/home.html")

    except GREUser.DoesNotExist:
        return render(request, "cedepe/home.html")




from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm  # Certifique-se de importar corretamente
from monitoramento.models import GREUser  # Importa o modelo de usuário extendido

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


def user_logout(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")

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
