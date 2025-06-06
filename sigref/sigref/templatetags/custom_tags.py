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
