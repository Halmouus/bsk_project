import json
from django import template
from django.template.defaultfilters import floatformat
from decimal import InvalidOperation, Decimal

from testapp.utils import number_to_french_words


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
    
    try:
        # Convert to decimal for consistent handling
        if isinstance(value, str):
            value = value.replace(' ', '').replace(',', '.')
        value = Decimal(str(value))
        
        # Format with 2 decimal places
        formatted = '{:.2f}'.format(value)
        
        # Split into integer and decimal parts
        integer_part, decimal_part = formatted.split('.')
        
        # Format integer part with space separators
        int_with_spaces = ''
        for i, digit in enumerate(reversed(integer_part)):
            if i and i % 3 == 0:
                int_with_spaces = ' ' + int_with_spaces
            int_with_spaces = digit + int_with_spaces
            
        return f'{int_with_spaces}.{decimal_part}'
    except (ValueError, TypeError, InvalidOperation):
        return str(value)

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
        'UNPAID': 'Unpaid',
        'PARTIALLY_COMPENSATED': 'Partially Compensated'
    }
    return STATUS_DISPLAY.get(status_code, status_code)

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return value

@register.filter
def percentage(value, total):
    """Calculate percentage for progress bars"""
    try:
        return (float(value) / float(total)) * 100 if float(total) else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key), {'count': 0, 'expected': 0, 'discounted': 0, 'total': 0})

@register.filter
def sum_by(queryset, field):
    """Sum a specific field in a queryset or list of dicts"""
    if not queryset:
        return Decimal('0.00')
    return sum(Decimal(str(getattr(item, field, 0) or 0)) for item in queryset)

@register.filter(name='add_class')
def add_class(field, css_class):
    """Adds CSS class to form field"""
    return field.as_widget(attrs={'class': css_class})

@register.filter
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (TypeError, ValueError):
        return value    


@register.filter
def amount_to_words(value):
    return number_to_french_words(float(value))

@register.filter
def replace(value, arg):
    """Replace the first substring matching the argument with the second substring"""
    args = arg.split(':')
    if len(args) != 2:
        return value
    return value.replace(args[0], args[1])

@register.filter
def json_encode(data):
    """Encode data as JSON string"""
    return json.dumps(data)