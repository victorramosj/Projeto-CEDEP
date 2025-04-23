from django import template

register = template.Library()

@register.filter
def url_in(value, arg):
    url_list = arg.split(',')
    return value in url_list