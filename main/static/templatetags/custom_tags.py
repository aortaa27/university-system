from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return ''


@register.filter
def get_dict_value(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None