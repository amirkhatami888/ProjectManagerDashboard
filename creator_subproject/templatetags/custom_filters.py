from django import template
from datetime import timedelta

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

@register.filter
def timesince_timedelta(timedelta_obj):
    """
    Custom filter to format timedelta objects for display
    """
    if not timedelta_obj:
        return "فعال"
    
    if not isinstance(timedelta_obj, timedelta):
        return str(timedelta_obj)
    
    total_seconds = int(timedelta_obj.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} ثانیه پیش"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} دقیقه پیش"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} ساعت پیش"
    else:
        days = total_seconds // 86400
        return f"{days} روز پیش" 