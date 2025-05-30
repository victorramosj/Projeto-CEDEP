from django import forms
from .models import ProblemaUsuario
from monitoramento.models import Setor  # <- Corrigido aqui

class ProblemaUsuarioForm(forms.ModelForm):
    class Meta:
        model = ProblemaUsuario
        fields = ['setor', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva o problema...',
                'rows': 4
            }),
            'setor': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'descricao': 'Problema',
            'setor': 'Setor',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['setor'].queryset = Setor.objects.all()

