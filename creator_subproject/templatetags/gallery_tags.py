import base64
from django import template

register = template.Library()

@register.filter
def base64_encode(value):
    """
    Convert binary image data to base64 encoded string
    """
    if not value:
        return ''
    
    try:
        # Ensure value is bytes
        if not isinstance(value, bytes):
            value = bytes(value)
        
        # Encode to base64
        return base64.b64encode(value).decode('utf-8')
    except Exception as e:
        print(f"Base64 encoding error: {e}")
        return '' 