from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.views import LoginView
import logging

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    template_name = 'login.html'
    
    def form_valid(self, form):
        print(f"[CustomLoginView] Successful login for {form.get_user()}")
        messages.success(self.request, f'Welcome, {form.get_user().username}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        print(f"[CustomLoginView] Failed login attempt")
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

def login_view(request):
    print("[LoginView] Processing login request")
    
    # Redirect if already logged in
    if request.user.is_authenticated:
        print(f"[LoginView] User {request.user.username} already authenticated")
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"[LoginView] Login attempt for user: {username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print(f"[LoginView] Successful login for {username}")
            messages.success(request, f'Welcome back, {username}!')
            
            # Get next URL from POST data (hidden input in form)
            next_url = request.POST.get('next')
            if next_url and next_url != '/':
                print(f"[LoginView] Redirecting to: {next_url}")
                return redirect(next_url)
            return redirect('home')
        else:
            print(f"[LoginView] Failed login attempt for {username}")
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

@cache_control(no_cache=True, must_revalidate=True)
@login_required
def logout_view(request):
    print(f"[LogoutView] Processing logout for user: {request.user.username}")
    
    if request.user.is_authenticated:
        print("[LogoutView] User authenticated, proceeding with logout")
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    
    print("[LogoutView] Redirecting to login page")
    response = redirect('/')  # Redirect to root URL which is our login page
    
    # Prevent browser back button after logout
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@never_cache
@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def profile_view(request):
    print(f"[ProfileView] Accessing profile for {request.user.username}")
    return render(request, 'profile.html')