# testapp/templatetags/permission_tags.py - NEW FILE
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def has_permission(context, permission_name):
    """Check if user has specific permission"""
    try:
        user = context['request'].user
        return getattr(user.userprofile.role, permission_name, False)
    except Exception as e:
        print(f"[PermissionCheck] Error in template tag: {str(e)}")
        return False

@register.filter
def can_see_button(user, permission_name):
    """Filter to check button visibility"""
    try:
        return getattr(user.userprofile.role, permission_name, False)
    except Exception as e:
        print(f"[PermissionCheck] Button visibility check failed: {str(e)}")
        return False