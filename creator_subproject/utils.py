import re
from datetime import datetime
import jdatetime

def jalali_to_gregorian(jalali_date_str):
    """
    Convert a Jalali (Persian) date string to a Gregorian date.
    
    Args:
        jalali_date_str: String in format YYYY/MM/DD or YYYY-MM-DD
    
    Returns:
        datetime.date: The equivalent Gregorian date
    """
    if not jalali_date_str:
        return None
        
    # Clean the input string and normalize the format
    jalali_date_str = jalali_date_str.strip()
    
    # Check for different separators and standardize format
    if '-' in jalali_date_str:
        parts = jalali_date_str.split('-')
    elif '/' in jalali_date_str:
        parts = jalali_date_str.split('/')
    else:
        return None
        
    if len(parts) != 3:
        return None
        
    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        
        # Convert using jdatetime
        jalali_date = jdatetime.date(year=year, month=month, day=day)
        gregorian_date = jalali_date.togregorian()
        
        return gregorian_date
    except (ValueError, IndexError):
        return None

def gregorian_to_jalali(date_obj):
    """
    Convert Gregorian date object to Jalali date string (YYYY/MM/DD)
    """
    if not date_obj:
        return ''
        
    try:
        jdate = jdatetime.date.fromgregorian(date=date_obj)
        return jdate.strftime('%Y/%m/%d')
    except (ValueError, TypeError) as e:
        print(f"Error converting date {date_obj}: {e}")
        return '' 