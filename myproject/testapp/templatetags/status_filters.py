from django import template

register = template.Library()

@register.filter
def status_badge(status):
    """Returns appropriate badge class for receipt status"""
    status = str(status).lower()
    
    return {
        'portfolio': 'secondary',
        'presented_collection': 'info',
        'presented_discount': 'info',
        'discounted': 'success',
        'paid': 'success',
        'unpaid': 'danger',
        'rejected': 'danger',
        'compensated': 'warning'
    }.get(status, 'secondary')