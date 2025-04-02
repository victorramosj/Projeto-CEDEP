# forms.py
from django import forms
from .models import Quarto, Cama, Hospede, Ocupacao, Reserva

class QuartoForm(forms.ModelForm):
    class Meta:
        model = Quarto
        fields = ['numero', 'descricao']

class CamaForm(forms.ModelForm):
    class Meta:
        model = Cama
        fields = ['quarto', 'identificacao', 'status']

class HospedeForm(forms.ModelForm):
    class Meta:
        model = Hospede
        fields = ['nome', 'cpf', 'email', 'telefone', 'instituicao', 'endereco']

class OcupacaoForm(forms.ModelForm):  # Novo form para Ocupacao
    class Meta:
        model = Ocupacao
        fields = ['hospede', 'cama', 'data_checkin', 'data_checkout', 'status']

    def clean(self):
        cleaned_data = super().clean()
        cama = cleaned_data.get('cama')
        hospede = cleaned_data.get('hospede')
        data_checkin = cleaned_data.get('data_checkin')
        data_checkout = cleaned_data.get('data_checkout')
        status = cleaned_data.get('status')

        if cama and cama.status != 'DISPONIVEL':
            raise forms.ValidationError("A cama selecionada não está disponível.")

        if hospede and Ocupacao.objects.filter(hospede=hospede, status='ATIVA').exists():
            raise forms.ValidationError("Este hóspede já possui uma ocupação ativa.")

        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise forms.ValidationError("A data de check-in deve ser anterior à data de check-out.")

        if data_checkin and data_checkin < date.today():
            raise forms.ValidationError("A data de check-in não pode ser no passado.")

        return cleaned_data

    def save(self, commit=True):
        ocupacao = super().save(commit=False)

        if ocupacao.status == 'ATIVA':
            ocupacao.cama.status = 'OCUPADA'
        elif ocupacao.status in ['CANCELADA', 'FINALIZADA']:
            ocupacao.cama.status = 'DISPONIVEL'

        if commit:
            ocupacao.cama.save()
            ocupacao.save()

        return ocupacao

class ReservaForm(forms.ModelForm):  # Novo form para Reserva
    class Meta:
        model = Reserva
        fields = ['hospede', 'data_checkin', 'data_checkout', 'status']

    def clean(self):
        cleaned_data = super().clean()
        data_checkin = cleaned_data.get('data_checkin')
        data_checkout = cleaned_data.get('data_checkout')

        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise forms.ValidationError("A data de check-in deve ser anterior à data de check-out.")

        return cleaned_data

    def save(self, commit=True):
        return super().save(commit=commit)