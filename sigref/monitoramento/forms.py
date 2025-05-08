from django import forms
from .models import Resposta, Pergunta

class RespostaForm(forms.ModelForm):
    class Meta:
        model = Resposta
        fields = ['pergunta', 'resposta_sn', 'resposta_num', 'resposta_texto']
        widgets = {
            'pergunta': forms.HiddenInput(),
            'resposta_sn': forms.RadioSelect(choices=[(True, 'Sim'), (False, 'Não')]),
            'resposta_num': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'resposta_texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),            
        }
        labels = {
            'resposta_sn': 'Resposta',
            'resposta_num': 'Valor',
            'resposta_texto': 'Descrição',
            
        }
        

def RespostaFormSet(data=None, files=None, perguntas=None):
    """
    Gera forms customizados para cada pergunta
    """
    formset = []
    for idx, pergunta in enumerate(perguntas, start=1):
        initial = {'pergunta': pergunta}
        prefix = f"p_{pergunta.pk}"
        
        form = RespostaForm(
            data=data,
            files=files,
            prefix=prefix,
            initial=initial
        )
        
        # Customiza campos baseado no tipo de pergunta
        if pergunta.tipo_resposta == 'SN':
            form.fields['resposta_sn'].required = True
            form.fields['resposta_num'].widget = forms.HiddenInput()
            form.fields['resposta_texto'].widget = forms.HiddenInput()
        elif pergunta.tipo_resposta == 'NU':
            form.fields['resposta_num'].required = True
            form.fields['resposta_sn'].widget = forms.HiddenInput()
            form.fields['resposta_texto'].widget = forms.HiddenInput()
        else:
            form.fields['resposta_texto'].required = True
            form.fields['resposta_sn'].widget = forms.HiddenInput()
            form.fields['resposta_num'].widget = forms.HiddenInput()
        
        formset.append(form)
    
    return formset