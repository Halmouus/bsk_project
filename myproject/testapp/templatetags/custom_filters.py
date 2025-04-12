from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def status_badge(status):
    """
    Convert status to a bootstrap badge class
    """
    status_map = {
        'pending': 'badge-secondary',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'in_progress': 'badge-warning',
        'completed': 'badge-primary'
    }
    return status_map.get(status, 'badge-light')

@register.filter
def euro_format(value):
    """
    Format number with spaces as thousand separators and comma as decimal point.
    Example: 12345.67 becomes 12 345,67
    """
    if value is None:
        return ""
    
    # Convert to Decimal for precision
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Format with 2 decimal places
    formatted = '{:,.2f}'.format(value)
    
    # Replace commas with temp placeholder
    formatted = formatted.replace(',', 'COMMA')
    
    # Replace dots with commas (for decimal point)
    formatted = formatted.replace('.', ',')
    
    # Replace placeholder with spaces (for thousand separators)
    formatted = formatted.replace('COMMA', ' ')
    
    return formatted
