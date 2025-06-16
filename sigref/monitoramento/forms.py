from django import forms
from .models import Resposta, Pergunta

class RespostaForm(forms.ModelForm):
    class Meta:
        model = Resposta
        fields = ['pergunta', 'resposta_sn', 'resposta_num', 'resposta_texto']
        widgets = {
            'pergunta': forms.HiddenInput(),
            # REMOVER O WIDGET RadioSelect AQUI
            'resposta_num': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'resposta_texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),            
        }
        labels = {
            'resposta_sn': 'Resposta',
            'resposta_num': 'Valor',
            'resposta_texto': 'Descrição',
        }

class RespostaFormSet:
    def __init__(self, data=None, files=None, perguntas=None):
        self.forms = []
        self.perguntas = perguntas or []
        
        for pergunta in self.perguntas:
            initial = {'pergunta': pergunta}
            prefix = f"p_{pergunta.pk}"
            
            form = RespostaForm(
                data=data,
                files=files,
                prefix=prefix,
                initial=initial
            )
            
            # Configura campos baseado no tipo de pergunta
            if pergunta.tipo_resposta == 'SN':
                # CORREÇÃO: Alterar para CharField com choices
                form.fields['resposta_sn'] = forms.ChoiceField(
                    choices=[('S', 'Sim'), ('N', 'Não')],
                    widget=forms.RadioSelect,
                    required=True
                )
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
            
            self.forms.append(form)
    
    def is_valid(self):
        return all(form.is_valid() for form in self.forms)
    
    def __iter__(self):
        return iter(self.forms)
    
    def __getitem__(self, index):
        return self.forms[index]
    
    def __len__(self):
        return len(self.forms)