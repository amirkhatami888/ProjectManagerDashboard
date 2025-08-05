from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return "" 

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to the form field or string."""
    if hasattr(field, 'as_widget'):
        # Handle form field
        return field.as_widget(attrs={"class": css_class})
    else:
        # Handle string value
        return f'<span class="{css_class}">{field}</span>' 