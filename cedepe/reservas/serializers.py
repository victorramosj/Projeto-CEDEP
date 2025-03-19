from rest_framework import serializers
from .models import Quarto, Cama, Hospede, Reserva

class QuartoSerializer(serializers.ModelSerializer):
    camas_disponiveis = serializers.SerializerMethodField()

    class Meta:
        model = Quarto
        fields = [
            'id',
            'numero',
            'descricao',
            'camas_disponiveis',
            'criado_em',
            'atualizado_em'
        ]

    def get_camas_disponiveis(self, obj):
        # Usa o método definido no model para retornar a quantidade de camas disponíveis
        return obj.camas_disponiveis()


class CamaSerializer(serializers.ModelSerializer):
    reserva_atual = serializers.SerializerMethodField()
    
    class Meta:
        model = Cama
        fields = [
            'id',
            'quarto',
            'identificacao',
            'status',
            'reserva_atual',
            'criado_em',
            'atualizado_em'
        ]
    
    def get_reserva_atual(self, obj):
        reserva = obj.reserva_set.filter(status='ATIVA').first()
        if reserva:
            return {
                'id': reserva.id,
                'hospede': {
                    'id': reserva.hospede.id,
                    'nome': reserva.hospede.nome,
                    'cpf': reserva.hospede.cpf
                },
                'data_checkin': reserva.data_checkin,
                'data_checkout': reserva.data_checkout
            }
        return None


class HospedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospede
        fields = [
            'id',
            'nome',
            'cpf',
            'email',
            'telefone',
            'endereco',
            'instituicao',  
            'criado_em',
            'atualizado_em'
        ]



class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = [
            'id',
            'hospede',
            'cama',
            'data_checkin',
            'data_checkout',
            'status',
            'criado_em',
            'atualizado_em'
        ]

    def validate(self, data):
        # Validação para garantir que a data de check-in seja anterior à data de check-out
        if data['data_checkin'] >= data['data_checkout']:
            raise serializers.ValidationError("Data de check-in deve ser anterior à data de check-out.")

        # Se a reserva for ativa, deve verificar:
        # 1. Que a cama está disponível
        # 2. Que o hóspede não possua outra reserva ativa
        if data.get('status', 'ATIVA') == 'ATIVA':
            cama = data.get('cama')
            if cama.status != 'DISPONIVEL':
                raise serializers.ValidationError("A cama selecionada não está disponível para reserva.")

            hospede = data.get('hospede')
            if Reserva.objects.filter(hospede=hospede, status='ATIVA').exists():
                raise serializers.ValidationError("Este hóspede já possui uma reserva ativa.")

        return data
