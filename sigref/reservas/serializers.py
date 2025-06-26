# serializers.py
from rest_framework import serializers
from .models import Quarto, Cama, Hospede, Ocupacao, Reserva
from datetime import date

# --- Serializers Aninhados para Otimização ---

class HospedeNestedSerializer(serializers.ModelSerializer):
    """
    Serializer para ser usado em aninhamento, mostrando apenas campos essenciais do Hóspede.
    """
    class Meta:
        model = Hospede
        fields = ['id', 'nome', 'cpf', 'instituicao'] # Adicione outros campos importantes aqui se precisar

class OcupacaoNestedSerializer(serializers.ModelSerializer):
    """
    Serializer para a Ocupação quando aninhada dentro de Cama.
    Mostra detalhes do hóspede e datas.
    """
    hospede = HospedeNestedSerializer(read_only=True) # Usa o serializer aninhado para o hóspede

    class Meta:
        model = Ocupacao
        # Inclua apenas os campos relevantes para a exibição no mapa/modal da cama
        fields = ['id', 'hospede', 'data_checkin', 'data_checkout', 'status']

# --- Serializers Principais ---

class QuartoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Quarto, incluindo camas disponíveis.
    """
    # camas_disponiveis foi movido para o modelo Quarto para melhor performance e coesão
    # Se você realmente precisa disso no serializer, reavalie se não seria melhor
    # uma view dedicada para estatísticas ou um método mais eficiente.
    # Por enquanto, vou remover para focar no problema principal do mapa.
    # Se 'camas_disponiveis' é um método no seu modelo Quarto que retorna um int,
    # ele deve ser automaticamente incluído pelo ModelSerializer se estiver em 'fields'.
    # Caso contrário, seria um SerializerMethodField.
    
    # Exemplo se 'camas_disponiveis' fosse um SerializerMethodField que você quer retornar
    # camas_disponiveis = serializers.SerializerMethodField()

    class Meta:
        model = Quarto
        fields = [
            'id',
            'numero',
            'descricao',
            # 'camas_disponiveis', # Removido para simplificar, se for um método de modelo ele funciona sem isso
            'criado_em',
            'atualizado_em'
        ]
        
    # Se 'camas_disponiveis' fosse um método customizado do serializer:
    # def get_camas_disponiveis(self, obj):
    #     return obj.cama_set.filter(status='DISPONIVEL').count()


class CamaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Cama, incluindo a ocupação ativa atual.
    """
    # Adicionamos um campo customizado que irá buscar a ocupação ATIVA
    ocupacao_ativa = serializers.SerializerMethodField()
    quarto_numero = serializers.ReadOnlyField(source='quarto.numero') # Adiciona o número do quarto para fácil acesso

    class Meta:
        model = Cama
        fields = [
            'id',
            'quarto', # ID do quarto
            'quarto_numero', # Número do quarto (para exibição fácil)
            'identificacao',
            'status',
            'ocupacao_ativa', # Este campo conterá os detalhes da ocupação ativa
            'criado_em',
            'atualizado_em'
        ]

    def get_ocupacao_ativa(self, obj):
        """
        Retorna a ocupação ativa atual para esta cama, se houver.
        Prioriza a ocupação ATIVA mais recente, caso haja inconsistência de múltiplas ativas.
        """
        # Filtra por ocupações ativas para esta cama, ordenando pela mais recente para ser mais robusto
        ocupacao = obj.ocupacao_set.filter(status='ATIVA').order_by('-data_checkin').first()
        if ocupacao:
            # Serializa a ocupação usando o OcupacaoNestedSerializer
            return OcupacaoNestedSerializer(ocupacao, context=self.context).data
        return None # Retorna None se não houver ocupação ativa

class HospedeSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Hóspede.
    """
    class Meta:
        model = Hospede
        fields = '__all__' # Inclui todos os campos do modelo

class OcupacaoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Ocupacao.
    Permite leitura e escrita de hospede e cama por seus IDs,
    e aninha os detalhes para leitura.
    """
    hospede_details = HospedeNestedSerializer(source='hospede', read_only=True)
    cama_details = CamaSerializer(source='cama', read_only=True) # Pode ser simplificado se não precisar de tudo

    class Meta:
        model = Ocupacao
        fields = [
            'id',
            'hospede', 'hospede_details', # 'hospede' para escrita (ID), 'hospede_details' para leitura (objeto)
            'cama', 'cama_details',       # 'cama' para escrita (ID), 'cama_details' para leitura (objeto)
            'data_checkin',
            'data_checkout',
            'status',
            'criado_em',
            'atualizado_em'
        ]
        extra_kwargs = {
            'hospede': {'write_only': True}, # 'hospede' é apenas para escrita de ID
            'cama': {'write_only': True}     # 'cama' é apenas para escrita de ID
        }

    def validate(self, data):
        instance = self.instance # Instância atual sendo atualizada, se houver
        
        # Obter os valores potenciais para validação
        data_checkin = data.get('data_checkin', instance.data_checkin if instance else None)
        data_checkout = data.get('data_checkout', instance.data_checkout if instance else None)
        status = data.get('status', instance.status if instance else 'ATIVA')
        cama = data.get('cama', instance.cama if instance else None)
        hospede = data.get('hospede', instance.hospede if instance else None)

        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise serializers.ValidationError("Data de check-in deve ser anterior à data de check-out.")

        # Validação para status 'ATIVA'
        if status == 'ATIVA':
            if cama and cama.status != 'DISPONIVEL' and (not instance or instance.cama != cama or instance.status != 'ATIVA'):
                # Permite mudar o status da própria cama se já estiver ocupada por esta ocupação
                # Mas não permite ocupar uma cama que já está ocupada por outra ocupação
                if Ocupacao.objects.filter(cama=cama, status='ATIVA').exclude(pk=instance.pk if instance else None).exists():
                    raise serializers.ValidationError(f"A cama '{cama.identificacao}' já possui uma ocupação ativa.")
            
            if hospede and Ocupacao.objects.filter(hospede=hospede, status='ATIVA').exclude(pk=instance.pk if instance else None).exists():
                raise serializers.ValidationError("Este hóspede já possui uma ocupação ativa.")
        
        return data

    def create(self, validated_data):
        ocupacao = super().create(validated_data)
        # Lógica de atualização de status da cama é melhor tratada na ViewSet (perform_create)
        return ocupacao

    def update(self, instance, validated_data):
        # Captura o status antigo antes da atualização
        old_status = instance.status
        ocupacao = super().update(instance, validated_data)
        
        # A lógica de atualização de status da cama e finalização de outras ocupações
        # é melhor tratada na ViewSet (perform_update) para ter acesso à instância antiga
        # e evitar circularidade ou lógica duplicada.
        return ocupacao


class ReservaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Reserva.
    """
    hospede_details = HospedeNestedSerializer(source='hospede', read_only=True)
    quarto_details = QuartoSerializer(source='quarto', read_only=True) # Se precisar dos detalhes do quarto

    class Meta:
        model = Reserva
        fields = [
            'id',
            'hospede', 'hospede_details',
            'quarto', 'quarto_details',
            'data_checkin',
            'data_checkout',
            'status',
            'criado_em',
            'atualizado_em'
        ]
        extra_kwargs = {
            'hospede': {'write_only': True},
            'quarto': {'write_only': True}
        }

    def validate(self, data):
        instance = self.instance
        
        data_checkin = data.get('data_checkin', instance.data_checkin if instance else None)
        data_checkout = data.get('data_checkout', instance.data_checkout if instance else None)
        status = data.get('status', instance.status if instance else 'PENDENTE')
        hospede = data.get('hospede', instance.hospede if instance else None)

        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise serializers.ValidationError("Data de check-in deve ser anterior à data de check-out.")

        if status == 'CONFIRMADA':
            # Verifica se o hóspede já tem uma reserva CONFIRMADA
            if hospede and Reserva.objects.filter(hospede=hospede, status='CONFIRMADA').exclude(pk=instance.pk if instance else None).exists():
                raise serializers.ValidationError("Este hóspede já possui uma reserva confirmada.")

            # Você pode adicionar validação para verificar disponibilidade do quarto aqui,
            # mas isso pode ser complexo dependendo da sua regra de negócio (ex: quarto inteiro vs. camas).
            # Se uma reserva implica no quarto inteiro, você pode verificar se o quarto está livre
            # para o período. Se for apenas para controle de hóspedes, pode não ser necessário.
            
        return data