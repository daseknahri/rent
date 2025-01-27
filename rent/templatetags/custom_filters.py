from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Retrieves a value from a dictionary by its key.
    """
    return dictionary.get(key, 0)