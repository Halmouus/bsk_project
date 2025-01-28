from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('includes/language_switcher.html')
def language_switcher():
    return {'LANGUAGES': settings.LANGUAGES}