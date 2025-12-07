"""
A module that contains a template filter for a dictionary item.
"""

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key, 0)
