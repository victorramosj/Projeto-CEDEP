import os
import django
import random

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sigref.settings")
django.setup()

from django.contrib.auth.models import User
from monitoramento.models import (
    Setor, Escola, GREUser,
    Questionario, Pergunta, Monitoramento
)

# Limpeza inicial incluindo usuários de teste
def limpar_tabelas():
    print("Limpando dados existentes...")
    Monitoramento.objects.all().delete()
    Pergunta.objects.all().delete()
    Questionario.objects.all().delete()
    GREUser.objects.all().delete()
    Escola.objects.all().delete()
    Setor.objects.all().delete()
    # Remover todos os usuários criados (cuidado em produção!)
    User.objects.all().delete()

# Criação de setores hierárquicos

def criar_setores():
    setores_principais = {
        "CGGR": [],
        "CGAF": ["UDP", "NAS", "NAE", "FINANCEIRO"],
        "CGIP": [],
        "CGDE": ["PSICOLOGIA", "UJC", "NEEI", "EDUCACAO"],
        "CGPA": [], "NOB": [], "CTI": [], "GABINETE": [],
    }
    setores = {}
    for nome, subs in setores_principais.items():
        pai = Setor.objects.create(nome=nome)
        setores[nome] = pai
        for s in subs:
            setores[s] = Setor.objects.create(nome=s, parent=pai)
    print(f"Criados {Setor.objects.count()} setores.")
    return setores

# Criação de 21 escolas fictícias vinculadas a um gestor regional

def criar_escolas():
    nomes = [
        "Escola Municipal Alfazema", "Escola Estadual Beija-flor", "Escola Técnica Cedro",
        "CEI Damasceno", "Centro Educacional Estrela", "Escola Fundamental Girassol",
        "Escola Integrada Hibisco", "Colégio Íris", "Escola Jardim", "Escola Limoeiro",
        "Escola Mimoso", "Escola Nogueira", "Escola Oliveira", "Escola Pingo-de-Óleo",
        "Escola Quixaba", "Escola Rosa", "Colégio Salgueiro", "Escola Tucano",
        "Escola Uva", "Escola Violeta", "Escola Zangão"
    ]

    # Usuário único para todas as escolas
    regional = User.objects.create_user(
        username='gestor_regional',
        email='regional@escolas.local',
        password='senha1234'
    )

    escolas = []
    for i, nome in enumerate(nomes, start=1):
        inep = str(20000000 + i)
        escola = Escola.objects.create(
            nome=nome,
            inep=inep,
            email_escola=f"contato{i}@escolas.local",
            nome_gestor=f"Gestor {i}",
            email_gestor=f"gestor{i}@escolas.local",
            user=regional,
            endereco=f"Rua das Flores, {100+i} - Bairro Centro",
            telefone=f"(71) 9{random.randint(90000,99999)}-{random.randint(1000,9999)}",
            telefone_gestor=f"(71) 9{random.randint(90000,99999)}-{random.randint(1000,9999)}"
        )
        escolas.append(escola)

    print(f"Criadas {len(escolas)} escolas vinculadas ao usuário regional.")
    return escolas

# Criação de usuários GREUser para diferentes perfis
def criar_usuarios_gre(setores, escolas):
    # Admin e coordenador
    admin = User.objects.create_superuser('admin', 'admin@sigref.local', 'ThunderC9#@!')
    GREUser.objects.create(user=admin, tipo_usuario='ADMIN', nome_completo='Administrador Sistema')

    coord = User.objects.create_user('coordenador', 'coord@sigref.local', 'coord123')
    GREUser.objects.create(user=coord, tipo_usuario='COORDENADOR', nome_completo='Coordenador GRE')

    # Chefes de setor
    for nome, setor in setores.items():
        u = User.objects.create_user(
            username=f"chefe_{nome.lower()}",
            email=f"chefe_{nome.lower()}@sigref.local",
            password='senha123'
        )
        GREUser.objects.create(user=u, tipo_usuario='CHEFE_SETOR', setor=setor, nome_completo=f"Chefe {nome}")

    # Monitores (1 por escola)
    for idx, escola in enumerate(escolas, start=1):
        u = User.objects.create_user(
            username=f"monitor_{idx}",
            email=f"monitor{idx}@sigref.local",
            password='senha123'
        )
        gre = GREUser.objects.create(user=u, tipo_usuario='MONITOR', nome_completo=f"Monitor {idx}")
        gre.escolas.add(escola)

    # Técnico CEDEPE
    tce = User.objects.create_user('tce', 'tce@sigref.local', 'tce123')
    GREUser.objects.create(user=tce, tipo_usuario='CEDEPE', nome_completo='Técnico CEDEPE')

    print(f"Total GREUsers: {GREUser.objects.count()}")

# Questionários e perguntas

def criar_questionarios(setores, escolas):
    qs = []
    coord = User.objects.filter(greuser__tipo_usuario='COORDENADOR').first()
    for nome, setor in setores.items():
        q = Questionario.objects.create(
            titulo=f"Questionário {nome}",
            descricao=f"Avaliação {nome}",
            setor=setor,
            criado_por=coord
        )
        for e in random.sample(escolas, 5):
            q.escolas_destino.add(e)
        for ordem in range(1,4):
            Pergunta.objects.create(
                questionario=q,
                ordem=ordem,
                texto=f"Pergunta {ordem} de {nome}?",
                tipo_resposta=random.choice(['SN','NU','TX'])
            )
        qs.append(q)
    print(f"Criados {len(qs)} questionários.")
    return qs

# Monitoramentos

def criar_monitoramentos(qs):
    for q in qs:
        for e in q.escolas_destino.all():
            Monitoramento.objects.create(
                questionario=q,
                escola=e,
                frequencia=random.choice([c[0] for c in Monitoramento.FREQUENCIA_CHOICES])
            )
    print(f"Criados {Monitoramento.objects.count()} monitoramentos.")

# Execução principal

def main():
    limpar_tabelas()
    setores = criar_setores()
    escolas = criar_escolas()
    criar_usuarios_gre(setores, escolas)
    qs = criar_questionarios(setores, escolas)
    criar_monitoramentos(qs)
    print("População concluída com sucesso.")

if __name__ == '__main__':
    main()
