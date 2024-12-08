from django import template
import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.filter
def status_badge(status):
    """Returns appropriate badge class for presentation status"""
    # Convert status to lowercase for consistent mapping
    original_status = str(status)
    status = original_status.lower()
    
    logger.debug(f"status_badge filter called with original status: {original_status}")
    
    result = {
        'pending': 'secondary',
        'presented': 'info',
        'paid': 'success',
        'rejected': 'danger',
        'unpaid': 'danger',
        'portfolio': 'primary',
        'presented_collection': 'info',
        'presented_discount': 'info',
        'discounted': 'success',
        
        # Explicitly map uppercase statuses
        'UNPAID': 'danger',
        'PAID': 'success',
        'REJECTED': 'danger',
        'PRESENTED_COLLECTION': 'info',
        'PRESENTED_DISCOUNT': 'info',
        'DISCOUNTED': 'success',
    }.get(original_status, status)  # Try original status first, then fallback to lowercase
    
    logger.debug(f"Returning badge class: {result}")
    return result