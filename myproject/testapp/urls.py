from django.urls import path, include


from .views_users import initialize_user_profiles, user_management, user_activity, create_user, user_permissions

from .views_auth import login_view, profile_view, logout_view
from . import views
from .views_supplier import (
    SupplierDetailView, SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView, SupplierBalanceView
)

from .views_product import ( 
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductAjaxCreateView, ProductDetailsView
)

from .views_product import (
    AssetAccountListView, AssetAccountCreateView, AssetAccountUpdateView, AssetAccountDeleteView
)

from .views_invoice import (
    InvoiceListView, InvoiceCreateView, InvoiceUpdateView, InvoiceDeleteView, InvoiceDetailsView,
    product_autocomplete, AddProductToInvoiceView, EditProductInInvoiceView, ExportInvoicesView, UnexportInvoiceView,
    InvoicePaymentDetailsView, InvoiceAccountingSummaryView, LinkDeliveryNoteView, UnlinkDeliveryNoteView,
    LinkReceptionNoteView, UnlinkReceptionNoteView
)

from .views_notes import (
    DeliveryNoteListView, DeliveryNoteCreateView, DeliveryNoteUpdateView, DeliveryNoteDeleteView,
    AvailableDeliveryNotesView, ReceptionNoteListView, ReceptionNoteCreateView, ReceptionNoteUpdateView,
    ReceptionNoteDeleteView, AvailableReceptionNotesView
)

from .views_contract import (
    ContractListView, ContractFilterView, ContractCreateView, ContractSuspendDomiciliationView,
    ContractUpdateView, ContractDeleteView, ContractGenerateInvoicesView,
    ContractTerminateView, ContractActivateView, ContractHistoryView
)

from .views_checkers import (
    CheckAllocationView, CheckPrintView, CheckerListView, CheckerCreateView, CheckerDetailsView, CheckCreateView, CheckListView, CheckStatusView,
    invoice_autocomplete, supplier_autocomplete, CheckerDeleteView, CheckUpdateView, CheckCancelView, CheckActionView,
    CheckerFilterView, CheckFilterView, CheckDetailView, AvailableCheckersView, CheckerSignatureView, CheckerPositionStatusView
)

from .views_credit_notes import CreditNoteDetailsView, CreateCreditNoteView

from .views_bank import (
    BankAccountListView, BankAccountCreateView, 
    BankAccountDeactivateView, BankAccountFilterView, BankAccountUpdateView, BankAccountDeleteView, CashAccountingView, CashExpenseView, CashPaymentDetailView, CashPaymentDetailsView, CashStatementView, GetExpenseTypesView,
    bank_account_autocomplete, BankFeeCreateView, BankFeeDeleteView, PresentationAutocompleteView
)

from .views_bank import CashConfigurationView, CashDepositView, CashPaymentView
from .views_receipts import (
    ReceiptListView, ReceiptCreateView, ReceiptUpdateView, ReceiptDeleteView, ReceiptDetailView, client_autocomplete,
    entity_autocomplete, unpaid_receipt_autocomplete, ReceiptStatusUpdateView, UnpaidReceiptsView, ReceiptTimelineView,
    ReceiptFilterView, validate_receipt_number, validate_compensating_receipt, compensation_timeline
)

from .views_client import (
    client_management,
    list_clients,
    create_client,
    update_client,
    delete_client,
    validate_field,
    ClientSaleListView,
    create_sale,
    ClientCardView
)
from .views_entity import (
    list_entities, create_entity, update_entity, delete_entity
)
from .views_presentation import (
    PresentationDocumentDeleteView, PresentationDocumentUploadView, PresentationListView, PresentationCreateView, PresentationUpdateView, PresentationDeleteView,
    PresentationDetailView, AvailableReceiptsView, DiscountInfoView, PresentationFilterView
)

from .views_statement import (
    BankStatementView, AccountingView, ContractPaymentActionView, OtherOperationsView, CalendarView, CalendarForecastView, PendingForecastsView,
    SupplierForecastView
)

from .views_transfer import (
    CreateTransferView, DeleteTransferView
)

from .views_vat import (
    VATDeclarationDeleteView, VATDeductionDetailsView, VATListView, VATConfigurationView, VATDeclarationCreateView, VATDeclarationDetailView, 
    VATDeclarationProcessView, VATDeclarationDeclareView, VATDeclarationPayView, 
    VATPendingDeclarationsView, VATForecastView
)

from .views_pay import (
    PayConfigurationView, PayDeclarationDeclareView, PayDeclarationDeleteView, PayDeclarationItemCreateView, PayDeclarationItemDeleteView, PayDeclarationUpdateView, PayItemDeleteView, PayListView, PayItemListView, PayItemCreateView, PayItemUpdateView,
    PayDeclarationListView, PayDeclarationCreateView, PayDeclarationDetailView, PayAccountingView, PayAccountingView,
    PayDeclarationItemUpdateView, PayAccountingView, PayAccountingView, PayAccountingView, PayPendingDeclarationsView
)
from . import views_production

from .views import test_translation


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),

    
    path('change_language/', views.change_language, name='change_language'),

    # User Management URLs
    path('users/initialize/', initialize_user_profiles, name='initialize-user-profiles'),
    path('users/', user_management, name='user-management'),
    path('users/activity/', user_activity, name='user-activity'),
    path('users/create/', create_user, name='create-user'),
    path('users/<str:user_id>/permissions/', user_permissions, name='user-permissions'),

    # Suppliers URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),  # List all suppliers
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier-create'),  # Create a new supplier
    path('suppliers/<uuid:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),  # Update a supplier
    path('suppliers/<uuid:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),  # Delete a supplier
    path('suppliers/autocomplete/', supplier_autocomplete, name='supplier-autocomplete'),  # Autocomplete for suppliers
    path('suppliers/<uuid:pk>/balance/', SupplierBalanceView.as_view(), name='supplier-balance'),  # Get supplier balance
    path('suppliers/<uuid:pk>/view/', SupplierDetailView.as_view(), name='supplier-detail'),
 
    # Products URLs
    path('products/', ProductListView.as_view(), name='product-list'),  # List all products
    path('products/create/', ProductCreateView.as_view(), name='product-create'),  # Create a new product
    path('products/<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),  # Update a product
    path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),  # Delete a product
    path('products/<uuid:pk>/details/', ProductDetailsView.as_view(), name='product-details'),  # Details for a specific product
    path('products/ajax-create/', ProductAjaxCreateView.as_view(), name='product-ajax-create'),  # AJAX view for creating a new Product

    # Asset Accounts URLs
    path('asset-accounts/', AssetAccountListView.as_view(), name='asset-account-list'),
    path('asset-accounts/create/', AssetAccountCreateView.as_view(), name='asset-account-create'),
    path('asset-accounts/<uuid:pk>/update/', AssetAccountUpdateView.as_view(), name='asset-account-update'),
    path('asset-accounts/<uuid:pk>/delete/', AssetAccountDeleteView.as_view(), name='asset-account-delete'),

    # Invoices URLs
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
    path('invoices/link-delivery-note/', LinkDeliveryNoteView.as_view(), name='link-delivery-note'),
    path('invoices/unlink-delivery-note/', UnlinkDeliveryNoteView.as_view(), name='unlink-delivery-note'),
    path('invoices/link-reception-note/', LinkReceptionNoteView.as_view(), name='link-reception-note'),
    path('invoices/unlink-reception-note/', UnlinkReceptionNoteView.as_view(), name='unlink-reception-note'),
    
    # Add these new URL patterns
    path('delivery-notes/', DeliveryNoteListView.as_view(), name='delivery-note-list'),
    path('delivery-notes/create/', DeliveryNoteCreateView.as_view(), name='delivery-note-create'),
    path('delivery-notes/<uuid:pk>/edit/', DeliveryNoteUpdateView.as_view(), name='delivery-note-edit'),
    path('delivery-notes/<uuid:pk>/delete/', DeliveryNoteDeleteView.as_view(), name='delivery-note-delete'),
    path('delivery-notes/available/', AvailableDeliveryNotesView.as_view(), name='available-delivery-notes'),
    

    path('reception-notes/', ReceptionNoteListView.as_view(), name='reception-note-list'),
    path('reception-notes/create/', ReceptionNoteCreateView.as_view(), name='reception-note-create'),
    path('reception-notes/<uuid:pk>/edit/', ReceptionNoteUpdateView.as_view(), name='reception-note-edit'),
    path('reception-notes/<uuid:pk>/delete/', ReceptionNoteDeleteView.as_view(), name='reception-note-delete'),
    path('reception-notes/available/', AvailableReceptionNotesView.as_view(), name='available-reception-notes'),

    # Contracts URLs
    path('contracts/', ContractListView.as_view(), name='contract-list'),
    path('contracts/filter/', ContractFilterView.as_view(), name='contract-filter'),
    path('contracts/create/', ContractCreateView.as_view(), name='contract-create'),
    path('contracts/<uuid:pk>/', ContractUpdateView.as_view(), name='contract-detail'),
    path('contracts/<uuid:pk>/update/', ContractUpdateView.as_view(), name='contract-update'),
    path('contracts/<uuid:pk>/delete/', ContractDeleteView.as_view(), name='contract-delete'),
    path('contracts/<uuid:pk>/generate/', ContractGenerateInvoicesView.as_view(), name='contract-generate'),
    path('contracts/<uuid:pk>/terminate/', ContractTerminateView.as_view(), name='contract-terminate'),
    path('contracts/<uuid:pk>/activate/', ContractActivateView.as_view(), name='contract-activate'),
    path('contracts/<uuid:pk>/history/', ContractHistoryView.as_view(), name='contract-history'),
    # Checkers URLs
    path('checkers/', CheckerListView.as_view(), name='checker-list'),
    path('checkers/filter/', CheckerFilterView.as_view(), name='checker-filter'),
    path('checkers/create/', CheckerCreateView.as_view(), name='checker-create'),
    path('checkers/<uuid:pk>/details/', CheckerDetailsView.as_view(), name='checker-details'),
    path('checkers/<uuid:pk>/delete/', CheckerDeleteView.as_view(), name='checker-delete'),
    path('checkers/available/', AvailableCheckersView.as_view(), name='available-checkers'),
    path('checkers/<uuid:pk>/signatures/', CheckerSignatureView.as_view(), name='checker-signatures'),
    path('checkers/<uuid:pk>/sign/', CheckerSignatureView.as_view(), name='checker-sign'),
    path('checkers/<uuid:checker_id>/position-status/<int:position>/',
    CheckerPositionStatusView.as_view(),
    name='checker-position-status'),

    # Checks URLs
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
    path('checks/<uuid:pk>/allocations/', 
         CheckAllocationView.as_view(), 
         name='check-allocations'),
    path('checks/<uuid:pk>/allocations/<uuid:allocation_id>/', 
         CheckAllocationView.as_view(), 
         name='delete-allocation'),
    path('checks/<uuid:check_id>/print/', CheckPrintView.as_view(), name='check-print'),

    # Bank URLs
    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/create/', BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<uuid:pk>/edit/', BankAccountUpdateView.as_view(), name='bank-account-edit'),
    path('bank-accounts/<uuid:pk>/delete/', BankAccountDeleteView.as_view(), name='bank-account-delete'),
    path('bank-accounts/<uuid:pk>/deactivate/', 
         BankAccountDeactivateView.as_view(), name='bank-account-deactivate'),
    path('bank-accounts/filter/', 
         BankAccountFilterView.as_view(), name='bank-account-filter'),
    path('bank-accounts/autocomplete/', bank_account_autocomplete, name='bank-account-autocomplete'),

    # Bank Statement URLs
    path('bank-accounts/<uuid:pk>/statement/', 
         BankStatementView.as_view(), name='bank-statement'),
    path('bank-accounts/<uuid:pk>/accounting/', 
         AccountingView.as_view(), name='bank-accounting'),
    path('bank-accounts/<uuid:pk>/other-operations/', 
         OtherOperationsView.as_view(), name='other-operations'),

    # Transfer URLs
    path('bank-accounts/transfers/create/', 
         CreateTransferView.as_view(), name='create-transfer'),
    path('bank-accounts/transfers/<uuid:pk>/delete/', 
         DeleteTransferView.as_view(), name='delete-transfer'),

    # Bank Fees
    path('bank-accounts/fees/create/', 
         BankFeeCreateView.as_view(), name='create-bank-fee'),
    path('bank-accounts/fees/<uuid:pk>/delete/', 
         BankFeeDeleteView.as_view(), name='delete-bank-fee'),
    path('presentations/autocomplete/', 
         PresentationAutocompleteView.as_view(), name='presentation-autocomplete'),


    # Cash Management URLs
    path('cash/', CashConfigurationView.as_view(), name='cash-configuration'),
    path('cash/deposits/', CashDepositView.as_view(), name='cash-deposits'),
    path('cash/payment/<uuid:invoice_id>/', CashPaymentView.as_view(), name='get-cash-payment-details'),
    path('cash/payment/invoice/<uuid:invoice_id>/', CashPaymentDetailsView.as_view(), name='cash-payment-details'),
    path('cash/payments/', CashPaymentView.as_view(), name='cash-payments'),
    path('cash/expenses/', CashExpenseView.as_view(), name='cash-expenses'),
    path('cash/expense-types/', GetExpenseTypesView.as_view(), name='get-expense-types'),
    path('cash/statement/', CashStatementView.as_view(), name='cash-statement'),
    path('cash/accounting/', CashAccountingView.as_view(), name='cash-accounting'),
    path('cash/payment/detail/', CashPaymentDetailView.as_view(), name='cash-payment-detail'),


    # Client Management Page
    path('client-management/', client_management, name='client_management'),
    
    # Client API endpoints
    path('api/clients/', list_clients, name='list_clients'),
    path('api/clients/create/', create_client, name='create_client'),
    path('api/clients/<uuid:client_id>/update/', update_client, name='update_client'),
    path('api/clients/<uuid:client_id>/delete/', delete_client, name='delete_client'),
    path('api/validate/<str:field>/<str:value>/', validate_field, name='validate-field'),
    
    # Entity API endpoints
    path('api/entities/', list_entities, name='list_entities'),
    path('api/entities/create/', create_entity, name='create_entity'),
    path('api/entities/<uuid:entity_id>/update/', update_entity, name='update_entity'),
    path('api/entities/<uuid:entity_id>/delete/', delete_entity, name='delete_entity'),

    path('client/sales/', ClientSaleListView.as_view(), name='sale-list'),
    path('client/sales/create/', create_sale, name='create-sale'),
    path('clients/<uuid:pk>/card/', ClientCardView.as_view(), name='client-card'),
    path('client/autocomplete/', client_autocomplete, name='client-autocomplete'),

    # Receipt URLs
    path('receipts/', ReceiptListView.as_view(), name='receipt-list'),
    path('receipts/create/<str:receipt_type>/', ReceiptCreateView.as_view(), name='receipt-create'),
    path('receipts/edit/<str:receipt_type>/<uuid:pk>/', ReceiptUpdateView.as_view(), name='receipt-edit'),
    path('receipts/delete/<str:receipt_type>/<uuid:pk>/', ReceiptDeleteView.as_view(), name='receipt-delete'),
    path('receipts/details/<str:receipt_type>/<uuid:pk>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipts/unpaid/', UnpaidReceiptsView.as_view(), name='unpaid-receipts'),
    path('receipts/<str:receipt_type>/<uuid:pk>/status/', ReceiptStatusUpdateView.as_view(), 
        name='receipt-status-update'),
    path('receipts/<str:receipt_type>/<uuid:pk>/timeline/', 
        ReceiptTimelineView.as_view(), 
         name='receipt-timeline'),

    # Autocomplete endpoints for form fields
    path('receipts/client/autocomplete', client_autocomplete, name='client-autocomplete'),
    path('receipts/entity/autocomplete', entity_autocomplete, name='entity-autocomplete'),
    path('receipts/unpaid-autocomplete/', unpaid_receipt_autocomplete, name='unpaid-receipt-autocomplete'),

    # Filter receipts
    path('receipts/filter/', ReceiptFilterView.as_view(), name='receipt-filter'),
    path('receipts/validate-number/', validate_receipt_number, name='validate-receipt-number'),
    path('receipts/validate-compensating-receipt/', validate_compensating_receipt, name='validate-compensating-receipt'),
    path('receipts/<str:receipt_type>/<uuid:pk>/compensation-timeline/', compensation_timeline, name='compensation-timeline'),

    # Presentation URLs
    path('presentations/', PresentationListView.as_view(), name='presentation-list'),
    path('presentations/create/', PresentationCreateView.as_view(), name='presentation-create'),
    path('presentations/<uuid:pk>/', PresentationDetailView.as_view(), name='presentation-detail'),
    path('presentations/<uuid:pk>/edit/', PresentationUpdateView.as_view(), name='presentation-edit'),
    path('presentations/<uuid:pk>/delete/', PresentationDeleteView.as_view(), name='presentation-delete'),
    path('presentations/available-receipts/', AvailableReceiptsView.as_view(), name='available-receipts'),
    path('presentations/discount-info/<uuid:bank_account_id>/', 
        DiscountInfoView.as_view(), name='presentation-discount-info'),
    path('presentations/filter/', PresentationFilterView.as_view(), name='presentation-filter'),
    path('presentations/<uuid:pk>/upload-document/', 
        PresentationDocumentUploadView.as_view(), 
        name='presentation-upload-document'),
    path('presentations/<uuid:pk>/delete-document/', 
        PresentationDocumentDeleteView.as_view(), 
        name='presentation-delete-document'),

    # Calendar URLs
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('calendar/forecasts/', CalendarForecastView.as_view(), name='calendar-forecasts'),
    path('calendar/supplier-forecasts/', SupplierForecastView.as_view(), name='supplier_forecasts'),
    path('calendar/vat-forecasts/', VATForecastView.as_view(), name='vat-forecasts'),

    path('bank/pending-forecasts/<str:bank_id>/', PendingForecastsView.as_view(), name='pending_forecasts'),

    # Contract URLs
    path('contracts/<uuid:pk>/suspend-domiciliation/', 
         ContractSuspendDomiciliationView.as_view(), 
         name='contract-suspend-domiciliation'),
    path('bank/contracts/<uuid:contract_id>/payment-action/', 
        ContractPaymentActionView.as_view(), 
        name='contract-payment-action'),

    # VAT URLs
    path('vat/', VATListView.as_view(), name='vat-list'),
    path('vat/config/', VATConfigurationView.as_view(), name='vat-config'),
    path('vat/create/', VATDeclarationCreateView.as_view(), name='vat-create'),
    path('vat/<uuid:declaration_id>/', VATDeclarationDetailView.as_view(), name='vat-detail'),
    path('vat/<uuid:declaration_id>/process/', VATDeclarationProcessView.as_view(), name='vat-process'),
    path('vat/<uuid:declaration_id>/declare/', VATDeclarationDeclareView.as_view(), name='vat-declare'),
    path('vat/<uuid:declaration_id>/pay/', VATDeclarationPayView.as_view(), name='vat-pay'),
    path('vat/pending/', VATPendingDeclarationsView.as_view(), name='vat-pending'),
    path('vat/forecast/', VATForecastView.as_view(), name='vat-forecast'),
    path('vat/forecast/<int:year>/<int:month>/', VATForecastView.as_view(), name='vat-forecast-period'),
    path('vat/<uuid:declaration_id>/deductions/', 
        VATDeductionDetailsView.as_view(), 
        name='vat-deduction-details'),  
    path('vat/<uuid:declaration_id>/delete/', VATDeclarationDeleteView.as_view(),name='vat-delete'),

    # Pay URLs    
    path('pay/config/', PayConfigurationView.as_view(), name='pay-config'),
    path('pay/', PayListView.as_view(), name='pay-list'),
    path('pay/items/', PayItemListView.as_view(), name='pay-item-list'),
    path('pay/items/create/', PayItemCreateView.as_view(), name='pay-item-create'),
    path('pay/items/<uuid:pk>/edit/', PayItemUpdateView.as_view(), name='pay-item-edit'),
    path('pay/items/<uuid:pk>/delete/', PayItemDeleteView.as_view(), name='pay-item-delete'),
    path('pay/declarations/', PayDeclarationListView.as_view(), name='pay-declaration-list'),
    path('pay/declarations/create/', PayDeclarationCreateView.as_view(), name='pay-declaration-create'),
    path('pay/declarations/<uuid:pk>/', PayDeclarationDetailView.as_view(), name='pay-declaration-detail'),
    path('pay/declarations/<uuid:pk>/edit/', PayDeclarationUpdateView.as_view(), name='pay-declaration-edit'),
    path('pay/declarations/<uuid:pk>/delete/', PayDeclarationDeleteView.as_view(), name='pay-declaration-delete'),
    path('pay/accounting/', PayAccountingView.as_view(), name='pay-accounting'),
    path('pay/declarations/<uuid:pk>/items/create/', PayDeclarationItemCreateView.as_view(), name='pay-declaration-item-create'),
    path('pay/declarations/<uuid:pk>/items/<uuid:item_pk>/edit/', PayDeclarationItemUpdateView.as_view(), name='pay-declaration-item-edit'),
    path('pay/declarations/<uuid:pk>/items/<uuid:item_pk>/delete/', PayDeclarationItemDeleteView.as_view(), name='pay-declaration-item-delete'),
    path('pay/pending/', PayPendingDeclarationsView.as_view(), name='pay-pending'),
    path('pay/declarations/<uuid:pk>/declare/', PayDeclarationDeclareView.as_view(), name='pay-declaration-declare'),


    # Production Dashboard URLs
    path('production/dashboard/', views_production.DashboardView.as_view(), name='production-dashboard'),
    # Report API endpoint
    path('production/api/report-data/', views_production.report_data, name='production-report-data'),

    # Brick Management URLs
    path('production/brick-types/', views_production.BrickTypeListView.as_view(), name='brick-type-list'),
    path('production/brick-types/create/', views_production.BrickTypeCreateView.as_view(), name='brick-type-create'),
    path('production/brick-types/<uuid:pk>/detail/', views_production.BrickTypeDetailView.as_view(), name='brick-type-detail'),
    path('production/brick-types/<uuid:pk>/update/', views_production.BrickTypeUpdateView.as_view(), name='brick-type-update'),
    path('production/brick-types/<uuid:pk>/delete/', views_production.BrickTypeDeleteView.as_view(), name='brick-type-delete'),
    path('production/brick-types/<uuid:pk>/price-history/', views_production.BrickPriceHistoryView.as_view(), name='brick-price-history'),
    
    # Energy URLs   
    path('production/energy/', views_production.EnergyTypeListView.as_view(), name='energy-type-list'),
    path('production/energy/create/', views_production.EnergyTypeCreateView.as_view(), name='energy-type-create'),
    path('production/energy/<uuid:pk>/update/', views_production.EnergyTypeUpdateView.as_view(), name='energy-type-update'),
    path('production/energy/<uuid:pk>/delete/', views_production.EnergyTypeDeleteView.as_view(), name='energy-type-delete'),
    path('production/energy/<uuid:pk>/price-history/', views_production.EnergyPriceHistoryView.as_view(), name='energy-price-history'),
    path('production/energy/<uuid:pk>/detail/', views_production.EnergyTypeDetailView.as_view(), name='energy-type-detail'),

    # Production Batch URLs
    path('production/records/', views_production.ProductionBatchListView.as_view(), name='production-list'),
    path('production/records/create/', views_production.ProductionBatchCreateView.as_view(), name='production-create'),
    path('production/records/<uuid:pk>/detail/', views_production.ProductionBatchDetailView.as_view(), name='production-detail'),
    path('production/records/<uuid:pk>/update/', views_production.ProductionBatchUpdateView.as_view(), name='production-update'),
    path('production/records/<uuid:pk>/delete/', views_production.ProductionBatchDeleteView.as_view(), name='production-delete'),

    # API endpoints for production data
    path('production/records/latest-date/', views_production.LatestProductionDateView.as_view(), name='production-latest-date'),
    path('production/api/current-stock/', views_production.CurrentStockView.as_view(), name='production-current-stock'),
    path('production/api/historical-stock/', views_production.HistoricalStockView.as_view(), name='historical-stock'),
    
    # Loading Record URLs
    path('production/loading/', views_production.LoadingRecordListView.as_view(), name='loading-list'),
    path('production/loading/create/', views_production.LoadingRecordCreateView.as_view(), name='loading-create'),
    path('production/loading/<uuid:pk>/detail/', views_production.LoadingRecordDetailView.as_view(), name='loading-detail'),
    path('production/loading/<uuid:pk>/update/', views_production.LoadingRecordUpdateView.as_view(), name='loading-update'),
    path('production/loading/<uuid:pk>/delete/', views_production.LoadingRecordDeleteView.as_view(), name='loading-delete'),
    path('production/loading/latest-date/', views_production.LatestLoadingDateView.as_view(), name='loading-latest-date'),

    # test translation
    path('test-translation/<str:lang>/', test_translation, name='test-translation'),

]
