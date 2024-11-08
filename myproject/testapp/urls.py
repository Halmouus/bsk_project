from django.urls import path
from . import views
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView

urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view

    # Supplier CRUD operations
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),  # List all suppliers
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier-create'),  # Create a new supplier
    path('suppliers/<uuid:pk>/update/', views.SupplierUpdateView.as_view(), name='supplier-update'),  # Update a supplier
    path('suppliers/<uuid:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier-delete'),  # Delete a supplier
]
