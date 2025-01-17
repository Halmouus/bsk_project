from django.shortcuts import redirect

class RedirectIfNotLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"[AuthMiddleware] Processing request for path: {request.path}")
        
        # Define paths that don't require authentication
        public_paths = ['/admin/']  # Remove '/login/' since we want to handle '/' differently
        current_path = request.path
        
        # Special handling for root URL
        if current_path == '/' and request.user.is_authenticated:
            print("[AuthMiddleware] Authenticated user at root URL - redirecting to home")
            return redirect('home')
            
        # If user is not authenticated and not accessing a public path
        if not request.user.is_authenticated and current_path != '/' and not any(current_path.startswith(path) for path in public_paths):
            print(f"[AuthMiddleware] Unauthenticated access attempt to: {current_path}")
            # Store the current path for redirect after login
            next_url = current_path
            redirect_url = '/'
            if next_url:
                redirect_url += f'?next={next_url}'
            print(f"[AuthMiddleware] Redirecting to: {redirect_url}")
            return redirect(redirect_url)
            
        return self.get_response(request)
