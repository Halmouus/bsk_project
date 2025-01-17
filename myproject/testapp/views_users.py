from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserRole, UserProfile, UserActivity, User
import logging
from django.core.exceptions import PermissionDenied
from functools import wraps

logger = logging.getLogger(__name__)


def initialize_user_profiles(request):
    """One-time function to setup profiles for existing users"""
    print("[UserInit] Setting up user profiles")
    
    # First create a default admin role if it doesn't exist
    admin_role, created = UserRole.objects.get_or_create(
        name='Admin',
        defaults={
            'description': 'Full system access',
            'can_manage_users': True,
            'can_view_bank': True,
            'can_manage_bank': True,
            'can_view_checks': True,
            'can_manage_checks': True,
            'can_view_clients': True,
            'can_manage_clients': True,
            'can_view_suppliers': True,
            'can_manage_suppliers': True
        }
    )
    
    # Create profiles for users that don't have one
    users_without_profiles = User.objects.filter(userprofile__isnull=True)
    print(f"[UserInit] Found {users_without_profiles.count()} users without profiles")
    
    for user in users_without_profiles:
        print(f"[UserInit] Creating profile for {user.username}")
        UserProfile.objects.create(
            user=user,
            role=admin_role,  # Give them admin role by default
            is_active=user.is_active
        )
    
    return JsonResponse({
        'message': 'User profiles initialized',
        'profiles_created': users_without_profiles.count()
    })

def user_has_permission(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            profile = request.user.userprofile
            if not profile.role.can_manage_users:
                print(f"[UserManagement] Access denied for user {request.user.username}")
                return render(request, 'unauthorized.html', {
                    'reason': 'You need administrator permissions to access user management.'
                })
        except UserProfile.DoesNotExist:
            return render(request, 'unauthorized.html', {
                'reason': 'User profile not found. Please contact an administrator.'
            })
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@user_has_permission
def user_management(request):
    print(f"[UserManagement] Accessing user management view")
    
    users = UserProfile.objects.select_related('user', 'role').all()
    roles = UserRole.objects.all()
    
    context = {
        'users': users,
        'roles': roles
    }
    
    return render(request, 'users/user_management.html', context)

@login_required
@user_has_permission
def user_activity(request):
    print(f"[UserActivity] Accessing activity logs")
    
    activities = UserActivity.objects.select_related('user').order_by('-created_at')
    
    return render(request, 'users/activity_log.html', {
        'activities': activities
    })

@login_required
@user_has_permission
def create_user(request):
    if not request.user.userprofile.role.can_manage_users:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'error': 'Permission denied',
                'message': 'You need administrator permissions to create users.'
            }, status=403)
        return render(request, 'unauthorized.html', {
            'reason': 'You need administrator permissions to create users.'
        })

    if request.method == 'POST':
        print("[UserManagement] Creating new user")
        try:
            # Create user
            user = User.objects.create_user(
                username=request.POST['username'],
                password=request.POST['password'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email']
            )
            
            # Create profile
            role = UserRole.objects.get(id=request.POST['role'])
            UserProfile.objects.create(
                user=user,
                role=role
            )
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='created_user',
                target_model='User',
                target_id=user.id,
                details={
                    'username': user.username,
                    'role': role.name
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            print(f"[UserManagement] Error creating user: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)

def api_permission_error(request, required_permission='can_manage_users'):
    # Check if the request expects JSON
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'error': 'Permission denied',
            'message': 'You do not have the required permissions to perform this action.',
            'required_permission': required_permission
        }, status=403)
    else:
        return render(request, 'unauthorized.html', {
            'reason': f'You need {required_permission.replace("_", " ")} permissions to access this feature.'
        })

@login_required
def some_api_view(request):
    if not request.user.userprofile.role.can_manage_users:
        return api_permission_error(request)
    # Rest of your view code