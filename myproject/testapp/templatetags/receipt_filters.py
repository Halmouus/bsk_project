from django import template

register = template.Library()

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