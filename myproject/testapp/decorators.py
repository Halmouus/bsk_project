from functools import wraps
import logging
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden

logger = logging.getLogger(__name__)

def role_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has a profile and required permission
            if not hasattr(request.user, 'userprofile'):
                return render(request, 'unauthorized.html', {
                    'reason': 'User profile not found. Please contact an administrator.'
                })

            # Get the permission check function
            has_permission = getattr(request.user.userprofile.role, permission, False)
            
            if not has_permission:
                return render(request, 'unauthorized.html', {
                    'reason': f'You need {permission.replace("_", " ")} permissions to access this page.'
                })
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 

def require_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            print(f"[PermissionCheck] Checking {permission_name} for {request.user.username}")
            try:
                profile = request.user.userprofile
                if not getattr(profile.role, permission_name):
                    print(f"[PermissionCheck] Access denied: {permission_name}")
                    return HttpResponseForbidden("You don't have permission to access this page.")
                return view_func(request, *args, **kwargs)
            except Exception as e:
                print(f"[PermissionCheck] Error checking permission: {str(e)}")
                return HttpResponseForbidden("Error checking permissions")
        return wrapper
    return decorator