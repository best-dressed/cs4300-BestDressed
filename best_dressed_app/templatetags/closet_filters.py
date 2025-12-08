""" item filters for wardrobe stuff"""
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get a value from a dictionary using a variable key.
    
    Usage in template: {{ my_dict|get_item:my_key }}
    
    This is needed because Django templates don't support bracket notation
    like dictionary[key] - they only support dot notation which doesn't work
    with variable keys.
    """
    return dictionary.get(key)
