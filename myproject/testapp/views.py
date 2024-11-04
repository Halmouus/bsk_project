from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')  # Use 'home.html' directly

def profile(request):
    return render(request, 'profile.html')  # Use 'profile.html' directly
