from django.urls import path
from . import views
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView
from .views_product import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductAjaxCreateView, ProductDetailsView
from .views_invoice import (
    InvoiceListView, InvoiceCreateView, InvoiceUpdateView, InvoiceDeleteView, InvoiceDetailsView,
    product_autocomplete, AddProductToInvoiceView, EditProductInInvoiceView, ExportInvoicesView, UnexportInvoiceView,
    InvoicePaymentDetailsView, InvoiceAccountingSummaryView
)
from .views_checkers import (
    CheckerListView, CheckerCreateView, CheckerDetailsView, CheckCreateView, CheckListView, CheckStatusView,
    invoice_autocomplete, supplier_autocomplete, CheckerDeleteView, CheckUpdateView, CheckCancelView, CheckActionView,
    CheckerFilterView, CheckFilterView, CheckDetailView, AvailableCheckersView, SignChecksView
)

from .views_credit_notes import CreditNoteDetailsView, CreateCreditNoteView

from .views_bank import (
    BankAccountListView, BankAccountCreateView, 
    BankAccountDeactivateView, BankAccountFilterView
)

urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view

    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),  # List all suppliers
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier-create'),  # Create a new supplier
    path('suppliers/<uuid:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),  # Update a supplier
    path('suppliers/<uuid:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),  # Delete a supplier
    path('suppliers/autocomplete/', supplier_autocomplete, name='supplier-autocomplete'),  # Autocomplete for suppliers

    path('products/', ProductListView.as_view(), name='product-list'),  # List all products
    path('products/create/', ProductCreateView.as_view(), name='product-create'),  # Create a new product
    path('products/<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),  # Update a product
    path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),  # Delete a product
    path('products/<uuid:pk>/details/', ProductDetailsView.as_view(), name='product-details'),  # Details for a specific product
    path('products/ajax-create/', ProductAjaxCreateView.as_view(), name='product-ajax-create'),  # AJAX view for creating a new Product

    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),  # List all invoices
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),  # Create a new invoice
    path('invoices/<uuid:pk>/update/', InvoiceUpdateView.as_view(), name='invoice-update'),  # Update an invoice
    path('invoices/<uuid:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice-delete'),  # Delete an invoice
    path('products/autocomplete/', product_autocomplete, name='product-autocomplete'),  # Autocomplete for products
    path('invoices/details/', InvoiceDetailsView.as_view(), name='invoice-details'),  # Details for a specific invoice
    path('invoices/add-product/', AddProductToInvoiceView.as_view(), name='add-product-to-invoice'),  # Add a product to an invoice
    path('invoices/edit-product/<uuid:pk>/', EditProductInInvoiceView.as_view(), name='invoice-edit-product'),  # Edit a product in an invoice
    path('invoices/export/', ExportInvoicesView.as_view(), name='export-invoices'),
    path('invoices/<uuid:invoice_id>/unexport/', UnexportInvoiceView.as_view(), name='unexport-invoice'),
    path('invoices/<str:pk>/payment-details/', InvoicePaymentDetailsView.as_view(), name='invoice-payment-details'),
    path('invoices/<str:invoice_id>/accounting-summary/', InvoiceAccountingSummaryView.as_view(), name='invoice-accounting-summary'),
    path('invoices/autocomplete/', invoice_autocomplete, name='invoice-autocomplete'),
    path('invoices/<str:invoice_id>/credit-note-details/', CreditNoteDetailsView.as_view(), name='credit-note-details'),
    path('invoices/create-credit-note/', 
         CreateCreditNoteView.as_view(), 
         name='create-credit-note'),

    path('checkers/', CheckerListView.as_view(), name='checker-list'),  # List all checkers
    path('checkers/filter/', CheckerFilterView.as_view(), name='checker-filter'),
    path('checkers/create/', CheckerCreateView.as_view(), name='checker-create'),
    path('checkers/<uuid:pk>/details/', CheckerDetailsView.as_view(), name='checker-details'),
    path('checkers/<uuid:pk>/delete/', CheckerDeleteView.as_view(), name='checker-delete'),
    path('checkers/available/', AvailableCheckersView.as_view(), name='available-checkers'),

    path('checks/create/', CheckCreateView.as_view(), name='check-create'),
    path('checks/', CheckListView.as_view(), name='check-list'),
    path('checks/<uuid:pk>/mark-delivered/', 
        CheckStatusView.as_view(), {'action': 'delivered'}, name='check-mark-delivered'),
    path('checks/<uuid:pk>/mark-paid/', 
        CheckStatusView.as_view(), {'action': 'paid'}, name='check-mark-paid'),
    path('checks/<uuid:pk>/action/', CheckActionView.as_view(), name='check-action'),
    path('checks/<uuid:check_id>/details/', CheckDetailView.as_view(), name='check-details'),
    path('checks/<uuid:pk>/', CheckUpdateView.as_view(), name='check-update'),
    path('checks/<uuid:pk>/cancel/', CheckCancelView.as_view(), name='check-cancel'),
    path('checks/filter/', CheckFilterView.as_view(), name='check-filter'),
    path('checks/sign/', SignChecksView.as_view(), name='sign-checks'),


    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/create/', BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<uuid:pk>/deactivate/', 
         BankAccountDeactivateView.as_view(), name='bank-account-deactivate'),
    path('bank-accounts/filter/', 
         BankAccountFilterView.as_view(), name='bank-account-filter'),

]
