from django import template
import jdatetime
from datetime import datetime

register = template.Library()

@register.filter
def to_jalali(gregorian_date, format_str='%Y/%m/%d'):
    """Convert Gregorian date to Jalali (Persian) date with the specified format."""
    if not gregorian_date:
        return ""
    
    try:
        if isinstance(gregorian_date, str):
            # If it's a string, try to parse it as a date
            try:
                gregorian_date = datetime.strptime(gregorian_date, '%Y-%m-%d').date()
            except ValueError:
                # If parsing fails, return the original string
                return gregorian_date
        
        # Convert to Jalali date
        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return jalali_date.strftime(format_str)
    except Exception as e:
        # Return original in case of any error
        return f"{gregorian_date}" 