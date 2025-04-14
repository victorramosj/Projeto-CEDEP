from django.db import models

class Quarto(models.Model):
    """ Representa um quarto que contém várias camas. """
    numero = models.CharField(max_length=10, unique=True)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def camas_disponiveis(self):
        return self.camas.filter(status='DISPONIVEL').count()

    def __str__(self):
        return f"Quarto {self.numero}"

class Cama(models.Model):
    """ Representa uma cama dentro de um quarto. """
    STATUS = (
        ('DISPONIVEL', 'Disponível'),
        ('OCUPADA', 'Ocupada'),
    )
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name="camas")
    identificacao = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS, default='DISPONIVEL')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.identificacao} - {self.quarto.numero} ({self.get_status_display()})"

from django.db import models

class Hospede(models.Model):
    """ Representa um hóspede. """
    nome = models.CharField(max_length=100, blank=True, default="Não informado")
    cpf = models.CharField(max_length=14, default="Não informado", blank=True, null=True)
    email = models.EmailField(blank=True, default="Não informado")
    telefone = models.CharField(max_length=20, blank=True, default="Não informado")
    endereco = models.TextField(blank=True, default="Não informado")
    instituicao = models.CharField(max_length=150, blank=True, default="Não informado")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome or "Hóspede sem nome"



class Ocupacao(models.Model):
    """ Representa a ocupação efetiva de uma cama (antiga Reserva). """
    STATUS = (
        ('ATIVA', 'Ativa'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    )
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE)
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE)
    data_checkin = models.DateField()
    data_checkout = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default='ATIVA')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.status == 'ATIVA':
            self.cama.status = 'OCUPADA'
        else:
            self.cama.status = 'DISPONIVEL'
        self.cama.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ocupação {self.id} - {self.hospede.nome} ({self.cama})"

class Reserva(models.Model):
    """ Nova tabela para intenções de reserva sem ocupar cama. """
    STATUS = (
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    )
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE)    
    data_checkin = models.DateField()
    data_checkout = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default='PENDENTE')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reserva {self.id} - {self.hospede.nome} ({self.quarto.numero})"