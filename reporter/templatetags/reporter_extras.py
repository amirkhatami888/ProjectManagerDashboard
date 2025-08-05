from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """
    Template filter to get a value from a dictionary by key.
    Usage: {{ my_dict|get:key_var }}
    """
    if dictionary is None:
        return None
    
    # Try to get the value for the key
    return dictionary.get(key) 

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get a value from a dictionary by key.
    Usage: {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None
    
    # Try to get the value for the key
    return dictionary.get(key) 