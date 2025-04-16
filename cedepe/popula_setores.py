import os
import django

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cedepe.settings")
django.setup()

from monitoramento.models import Setor

def limpar_setores():
    print("Limpando setores existentes...")
    Setor.objects.all().delete()

def criar_setores():
    setores_principais = {
        "CGGR": [],
        "CGAF": ["UDP", "NAS", "NAE", "FINANCEIRO"],
        "CGIP": [],
        "CGDE": ["PSICOLOGIA", "UJC", "NEEI", "EDUCACAO"],
        "CGPA": [],
        "NOB": [],
        "CTI": [],
        "GABINETE": [],
    }

    total_setores = 0
    total_subs = 0

    for nome_setor, subsetores in setores_principais.items():
        setor = Setor.objects.create(nome=nome_setor.upper())
        total_setores += 1
        for sub in subsetores:
            Setor.objects.create(nome=sub.upper(), parent=setor)
            total_subs += 1

    return total_setores, total_subs

def main():
    limpar_setores()
    total_setores, total_subs = criar_setores()
    
    print("\nResumo da população de setores:")
    print(f"- Setores principais: {total_setores}")
    print(f"- Subsetores criados: {total_subs}")
    print(f"- Total de registros em Setor: {Setor.objects.count()}")

if __name__ == "__main__":
    main()
