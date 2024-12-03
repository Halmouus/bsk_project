from django import template
import logging

logger = logging.getLogger(__name__)

register = template.Library()

logger.info("Loading presentation_filters.py")

@register.filter
def status_badge(status):
    """Returns appropriate badge class for presentation status"""
    logger.debug(f"status_badge filter called with status: {status}")
    result = {
        'pending': 'secondary',
        'presented': 'info',
        'paid': 'success',
        'rejected': 'danger',
        'PORTFOLIO': 'primary',
        'PRESENTED_COLLECTION': 'info',
        'PRESENTED_DISCOUNT': 'info',
        'PAID': 'success',
        'REJECTED': 'danger',
        'DISCOUNTED': 'success'
    }.get(status, 'secondary')
    logger.debug(f"Returning badge class: {result}")
    return result

# Print confirmation when module is loaded
print("presentation_filters.py loaded successfully")