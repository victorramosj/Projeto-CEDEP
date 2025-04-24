from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Digite seu nome de usuário",
            "autocomplete": "username"
        }),
        help_text="Requerido. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas.",
    )
    
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Digite seu e-mail",
            "autocomplete": "email"
        }),
        help_text="Digite um endereço de e-mail válido.",
    )
    
    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Digite sua senha",
            "autocomplete": "new-password"
        }),
        help_text="Sua senha deve conter pelo menos 8 caracteres.",
    )
    
    password2 = forms.CharField(
        label="Confirmação de Senha",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirme sua senha",
            "autocomplete": "new-password"
        }),
        help_text="Digite a mesma senha para verificação.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dicionário de ícones para cada campo
        field_icons = {
            "username": "person",
            "email": "envelope",
            "password1": "lock",
            "password2": "lock-fill",
        }
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.required:
                field.label = f"{field.label} *"
            
            # Adiciona o ícone como atributo extra no campo
            field.icon = field_icons.get(field_name, "tag")  # Usa "tag" como padrão se não houver ícone definido


from django import forms

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu e-mail'})
    )
