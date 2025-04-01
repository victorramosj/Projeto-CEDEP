# reservas/forms.py
from django import forms
from .models import Quarto, Cama, Hospede, Reserva

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

from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Reserva, Cama, Hospede

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['hospede', 'cama', 'data_checkin', 'data_checkout', 'status']

    def clean(self):
        cleaned_data = super().clean()
        cama = cleaned_data.get('cama')
        hospede = cleaned_data.get('hospede')
        data_checkin = cleaned_data.get('data_checkin')
        data_checkout = cleaned_data.get('data_checkout')
        status = cleaned_data.get('status')

        # Verifica se a cama está disponível
        if cama and cama.status != 'DISPONIVEL':
            raise ValidationError("A cama selecionada não está disponível para reserva.")

        # Verifica se o hóspede já tem uma reserva ativa
        if hospede and Reserva.objects.filter(hospede=hospede, status='ATIVA').exists():
            raise ValidationError("Este hóspede já possui uma reserva ativa.")

        # Verifica se a data de check-in é anterior à data de check-out
        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise ValidationError("A data de check-in deve ser anterior à data de check-out.")

        # Verifica se a data de check-in não é no passado
        if data_checkin and data_checkin < date.today():
            raise ValidationError("A data de check-in não pode ser no passado.")

        return cleaned_data

    def save(self, commit=True):
        reserva = super().save(commit=False)

        # Atualiza o status da cama: somente marca como ocupada se o check-in for hoje
        if reserva.status == 'ATIVA':
            hoje = date.today()
            if reserva.data_checkin == hoje:
                reserva.cama.status = 'OCUPADA'
            else:
                reserva.cama.status = 'DISPONIVEL'
        elif reserva.status in ['CANCELADA', 'FINALIZADA']:
            reserva.cama.status = 'DISPONIVEL'

        if commit:
            reserva.cama.save()  # Salva o novo status da cama
            reserva.save()       # Salva a reserva

        return reserva
