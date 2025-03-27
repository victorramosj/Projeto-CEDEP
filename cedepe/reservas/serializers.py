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

from datetime import date

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
        # Recupera a instância atual (para atualizações parciais)
        instance = self.instance
        
        # Usa o valor enviado ou o valor atual da instância
        data_checkin = data.get('data_checkin', instance.data_checkin if instance else None)
        data_checkout = data.get('data_checkout', instance.data_checkout if instance else None)
        
        # Se ambos os valores estiverem definidos, faz a validação
        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise serializers.ValidationError("Data de check-in deve ser anterior à data de check-out.")

        # Se a reserva for ativa, as outras validações são aplicadas
        if data.get('status', instance.status if instance else 'ATIVA') == 'ATIVA':
            cama = data.get('cama', instance.cama if instance else None)
            if cama and cama.status != 'DISPONIVEL':
                raise serializers.ValidationError("A cama selecionada não está disponível para reserva.")

            hospede = data.get('hospede', instance.hospede if instance else None)
            if hospede and Reserva.objects.filter(hospede=hospede, status='ATIVA').exclude(id=instance.id if instance else None).exists():
                raise serializers.ValidationError("Este hóspede já possui uma reserva ativa.")

        return data

    def update(self, instance, validated_data):
        # Se o status for alterado para FINALIZADA, atualiza a data_checkout para a data atual
        if validated_data.get('status') == 'FINALIZADA':
            validated_data['data_checkout'] = date.today()
        return super().update(instance, validated_data)
