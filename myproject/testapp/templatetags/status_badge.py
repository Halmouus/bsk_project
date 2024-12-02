from django import template

register = template.Library()

@register.filter
def status_badge(status):
    """Returns the appropriate badge class for a given status."""
    badges = {
        "pending": "warning",
        "presented": "info",
        "paid": "success",
        "rejected": "danger",
    }
    return badges.get(status, "secondary")
