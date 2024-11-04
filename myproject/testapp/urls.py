from django.urls import path
from django.contrib.auth.views import LogoutView  # Import Django's built-in LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),  # Logout view
]
