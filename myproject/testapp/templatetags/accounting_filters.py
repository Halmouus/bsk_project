from django import template
from django.template.defaultfilters import floatformat
from decimal import InvalidOperation, Decimal


register = template.Library()

@register.filter
def sum_debit(entries):
    return sum(entry['debit'] or 0 for entry in entries)

@register.filter
def sum_credit(entries):
    return sum(entry['credit'] or 0 for entry in entries)

@register.filter
def space_thousands(value):
    """
    Formats a number with spaces as thousand separators and 2 decimal places
    Example: 1234567.89 becomes 1 234 567.89
    """
    if value is None:
        return ''
    
    # Format to 2 decimal places first
    formatted = floatformat(value, 2)
    
    # Split the number into integer and decimal parts
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
    else:
        integer_part, decimal_part = formatted, '00'

    # Add space thousand separators to integer part
    int_with_spaces = ''
    for i, digit in enumerate(reversed(integer_part)):
        if i and i % 3 == 0:
            int_with_spaces = ' ' + int_with_spaces
        int_with_spaces = digit + int_with_spaces

    return f'{int_with_spaces}.{decimal_part}'

@register.filter
def format_balance(value):
    """
    Formats a balance number without negative sign
    """
    if value is None:
        return ''
    
    try:
        # Convert string to Decimal if needed
        if isinstance(value, str):
            value = Decimal(value)
        
        # Now we can safely use abs()
        formatted = floatformat(abs(value), 2)
        
        # Add space thousand separators
        int_part, dec_part = formatted.split('.')
        int_with_spaces = ''
        for i, digit in enumerate(reversed(int_part)):
            if i and i % 3 == 0:
                int_with_spaces = ' ' + int_with_spaces
            int_with_spaces = digit + int_with_spaces
            
        return f'{int_with_spaces}.{dec_part}'
        
    except (TypeError, ValueError, InvalidOperation) as e:
        print(f"Error formatting balance: {e}, value: {value}, type: {type(value)}")
        return str(value)

@register.filter
def get_status_display(status_code):
    STATUS_DISPLAY = {
        'PORTFOLIO': 'In Portfolio',
        'PRESENTED_COLLECTION': 'Presented for Collection',
        'PRESENTED_DISCOUNT': 'Presented for Discount',
        'DISCOUNTED': 'Discounted',
        'PAID': 'Paid',
        'REJECTED': 'Rejected',
        'COMPENSATED': 'Compensated',
        'UNPAID': 'Unpaid'
    }
    return STATUS_DISPLAY.get(status_code, status_code)

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return value