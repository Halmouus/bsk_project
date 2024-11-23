from django import template

register = template.Library()

@register.filter
def status_badge(status):
    return {
        'pending': 'secondary',
        'delivered': 'warning',
        'paid': 'success',
        'cancelled': 'danger'
    }.get(status, 'secondary')