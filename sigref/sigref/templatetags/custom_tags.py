from django import template

register = template.Library()

@register.filter
def url_in(value, arg):
    url_list = arg.split(',')
    return value in url_list

from datetime import date


@register.filter
def days_until(value):
    if isinstance(value, date):
        delta = value - date.today()
        return delta.days
    return 0

@register.filter
def get_by_id(escolas, school_id):
    for e in escolas:
        if e.id == school_id:
            return e
    return None


@register.filter
def average(lista):
    try:
        return round(sum(lista) / len(lista), 2)
    except:
        return 'N/A'
    
@register.filter(name='subtract')
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (TypeError, ValueError):
            return ''

        

from django.template.defaultfilters import floatformat
@register.filter(name='percentage')
def percentage(value, total):
    """Calcula a porcentagem de value em relação a total e formata com uma casa decimal."""
    try:
        if total == 0:
            return 0
        return floatformat((float(value) / float(total)) * 100, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return ''

@register.filter(name='color_rotate')
def color_rotate(counter):
    """Retorna uma cor baseada no índice fornecido."""
    colors = [
        "#FF5733",  # vermelho
        "#33FF57",  # verde
        "#3357FF",  # azul
        "#F1C40F",  # amarelo
        "#8E44AD",  # roxo
        "#16A085",  # teal
        "#E67E22",  # laranja
        "#2C3E50",  # azul escuro
    ]
    try:
        idx = int(counter) % len(colors)
        return colors[idx]
    except (ValueError, TypeError):
        return colors[0]