.
├── __init__.py
├── __pycache__
│   ├── __init__.cpython-38.pyc
│   ├── admin.cpython-38.pyc
│   ├── apps.cpython-38.pyc
│   ├── base.cpython-38.pyc
│   ├── decorators.cpython-38.pyc
│   ├── forms.cpython-38.pyc
│   ├── middleware.cpython-38.pyc
│   ├── models.cpython-38.pyc
│   ├── signals.cpython-38.pyc
│   ├── urls.cpython-38.pyc
│   ├── utils.cpython-38.pyc
│   ├── views.cpython-38.pyc
│   ├── views_auth.cpython-38.pyc
│   ├── views_bank.cpython-38.pyc
│   ├── views_checkers.cpython-38.pyc
│   ├── views_client.cpython-38.pyc
│   ├── views_contract.cpython-38.pyc
│   ├── views_credit_notes.cpython-38.pyc
│   ├── views_direct_debit.cpython-38.pyc
│   ├── views_entity.cpython-38.pyc
│   ├── views_invoice.cpython-38.pyc
│   ├── views_notes.cpython-38.pyc
│   ├── views_organism.cpython-38.pyc
│   ├── views_pay.cpython-38.pyc
│   ├── views_presentation.cpython-38.pyc
│   ├── views_product.cpython-38.pyc
│   ├── views_production.cpython-38.pyc
│   ├── views_receipts.cpython-38.pyc
│   ├── views_statement.cpython-38.pyc
│   ├── views_supplier.cpython-38.pyc
│   ├── views_transfer.cpython-38.pyc
│   ├── views_users.cpython-38.pyc
│   └── views_vat.cpython-38.pyc
├── admin.py
├── apps.py
├── base.py
├── codebase.md
├── decorators.py
├── file_structure.md
├── forms.py
├── management
│   ├── __init__.py
│   ├── __pycache__
│   │   └── __init__.cpython-38.pyc
│   └── commands
│       ├── __init__.py
│       ├── __pycache__
│       │   ├── __init__.cpython-38.pyc
│       │   ├── create_roles.cpython-38.pyc
│       │   ├── create_test_receipts.cpython-38.pyc
│       │   └── generate_test_data.cpython-38.pyc
│       ├── create_roles.py
│       ├── create_test_receipts.py
│       ├── generate_test_data.py
│       ├── populate_sample_data.py
│       └── reset_app.py
├── middleware.py
├── migrations
│   ├── 0001_initial.py
│   ├── 0002_remove_invoice_unique_supplier_invoice_ref_and_more.py
│   ├── 0003_accountingentry_bankstatement.py
│   ├── 0004_interbanktransfer_transferredrecord.py
│   ├── 0005_bankfeetype_bankfeetransaction.py
│   ├── 0006_bankfeetype_created_at_bankfeetype_updated_at_and_more.py
│   ├── 0007_checkreceipt_unpaid_date_lcn_unpaid_date.py
│   ├── 0008_alter_receipthistory_options_and_more.py
│   ├── 0009_alter_checkreceipt_check_number_alter_lcn_lcn_number_and_more.py
│   ├── 0010_alter_checkreceipt_status_alter_lcn_status_and_more.py
│   ├── 0011_alter_checkreceipt_status_alter_lcn_status_and_more.py
│   ├── 0012_alter_checkreceipt_status_alter_lcn_status_and_more.py
│   ├── 0013_alter_checkreceipt_status_alter_lcn_status_and_more.py
│   ├── 0014_remove_cashreceipt_compensating_content_type_and_more.py
│   ├── 0015_checkreceipt_rejection_cause_and_more.py
│   ├── 0016_presentationreceipt_forecast_payment_date_and_more.py
│   ├── 0017_forecaststatement_amount.py
│   ├── 0018_contract_alter_receipthistory_action_contractproduct_and_more.py
│   ├── 0019_check_is_supplier_payment_alter_check_cause_and_more.py
│   ├── 0020_remove_check_check_amount_cannot_exceed_due_and_more.py
│   ├── 0021_supplier_delay_check_supplier_delay_lcn.py
│   ├── 0022_remove_supplier_delay_check_and_more.py
│   ├── 0023_supplier_delay_check_supplier_delay_lcn.py
│   ├── 0024_check_printed_at.py
│   ├── 0025_contract_domiciliation_bank_and_more.py
│   ├── 0026_remove_contract_domiciliation_bank_and_more.py
│   ├── 0027_contract_domiciliation_bank_and_more.py
│   ├── 0028_directdebit.py
│   ├── 0029_alter_contractinvoice_invoice.py
│   ├── 0030_userrole_userprofile_useractivity.py
│   ├── 0031_userrole_can_manage_bank_accounts_and_more.py
│   ├── 0032_directdebit_contract_invoice_and_more.py
│   ├── 0033_remove_directdebit_contract_invoice_and_more.py
│   ├── 0034_vatdeclaration_cashreceipt_vat_declaration_period_and_more.py
│   ├── 0035_remove_invoice_non_deductible_vat_and_more.py
│   ├── 0036_invoice_non_deductible_vat_and_more.py
│   ├── 0037_alter_invoice_vat_deduction_rate.py
│   ├── 0038_alter_invoice_vat_deduction_rate.py
│   ├── 0039_invoice_doc_status_invoice_document_and_more.py
│   ├── 0040_paydeclaration_payitem_paydeclarationitem_and_more.py
│   ├── 0041_bankchecktemplate.py
│   ├── 0042_cashreceipt_document_checkreceipt_document_and_more.py
│   ├── 0043_bricktype_dailyproductionmetrics_loadingrecord_and_more.py
│   ├── 0044_energytype_alter_productionbatch_unique_together_and_more.py
│   ├── __init__.py
│   └── __pycache__
│       ├── 0001_initial.cpython-38.pyc
│       ├── 0002_remove_invoice_unique_supplier_invoice_ref_and_more.cpython-38.pyc
│       ├── 0003_accountingentry_bankstatement.cpython-38.pyc
│       ├── 0004_interbanktransfer_transferredrecord.cpython-38.pyc
│       ├── 0005_bankfeetype_bankfeetransaction.cpython-38.pyc
│       ├── 0006_bankfeetype_created_at_bankfeetype_updated_at_and_more.cpython-38.pyc
│       ├── 0007_checkreceipt_unpaid_date_lcn_unpaid_date.cpython-38.pyc
│       ├── 0008_alter_receipthistory_options_and_more.cpython-38.pyc
│       ├── 0009_alter_checkreceipt_check_number_alter_lcn_lcn_number_and_more.cpython-38.pyc
│       ├── 0010_alter_checkreceipt_status_alter_lcn_status_and_more.cpython-38.pyc
│       ├── 0011_alter_checkreceipt_status_alter_lcn_status_and_more.cpython-38.pyc
│       ├── 0012_alter_checkreceipt_status_alter_lcn_status_and_more.cpython-38.pyc
│       ├── 0013_alter_checkreceipt_status_alter_lcn_status_and_more.cpython-38.pyc
│       ├── 0014_remove_cashreceipt_compensating_content_type_and_more.cpython-38.pyc
│       ├── 0015_checkreceipt_rejection_cause_and_more.cpython-38.pyc
│       ├── 0016_presentationreceipt_forecast_payment_date_and_more.cpython-38.pyc
│       ├── 0017_forecaststatement_amount.cpython-38.pyc
│       ├── 0018_contract_alter_receipthistory_action_contractproduct_and_more.cpython-38.pyc
│       ├── 0019_check_is_supplier_payment_alter_check_cause_and_more.cpython-38.pyc
│       ├── 0020_remove_check_check_amount_cannot_exceed_due_and_more.cpython-38.pyc
│       ├── 0021_supplier_delay_check_supplier_delay_lcn.cpython-38.pyc
│       ├── 0022_remove_supplier_delay_check_and_more.cpython-38.pyc
│       ├── 0023_supplier_delay_check_supplier_delay_lcn.cpython-38.pyc
│       ├── 0024_check_printed_at.cpython-38.pyc
│       ├── 0025_contract_domiciliation_bank_and_more.cpython-38.pyc
│       ├── 0026_remove_contract_domiciliation_bank_and_more.cpython-38.pyc
│       ├── 0027_contract_domiciliation_bank_and_more.cpython-38.pyc
│       ├── 0028_directdebit.cpython-38.pyc
│       ├── 0029_alter_contractinvoice_invoice.cpython-38.pyc
│       ├── 0030_userrole_userprofile_useractivity.cpython-38.pyc
│       ├── 0031_userrole_can_manage_bank_accounts_and_more.cpython-38.pyc
│       ├── 0032_directdebit_contract_invoice_and_more.cpython-38.pyc
│       ├── 0033_remove_directdebit_contract_invoice_and_more.cpython-38.pyc
│       ├── 0034_vatdeclaration_cashreceipt_vat_declaration_period_and_more.cpython-38.pyc
│       ├── 0035_remove_invoice_non_deductible_vat_and_more.cpython-38.pyc
│       ├── 0036_invoice_non_deductible_vat_and_more.cpython-38.pyc
│       ├── 0037_alter_invoice_vat_deduction_rate.cpython-38.pyc
│       ├── 0038_alter_invoice_vat_deduction_rate.cpython-38.pyc
│       ├── 0039_invoice_doc_status_invoice_document_and_more.cpython-38.pyc
│       ├── 0040_paydeclaration_payitem_paydeclarationitem_and_more.cpython-38.pyc
│       ├── 0041_bankchecktemplate.cpython-38.pyc
│       ├── 0042_cashreceipt_document_checkreceipt_document_and_more.cpython-38.pyc
│       ├── 0043_bricktype_dailyproductionmetrics_loadingrecord_and_more.cpython-38.pyc
│       ├── 0044_energytype_alter_productionbatch_unique_together_and_more.cpython-38.pyc
│       └── __init__.cpython-38.pyc
├── models.py
├── services
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-38.pyc
│   │   ├── forecast.cpython-38.pyc
│   │   └── supplier_payment_forecast.cpython-38.pyc
│   ├── forecast.py
│   └── supplier_payment_forecast.py
├── services.py
├── signals.py
├── static
│   ├── css
│   │   ├── base.css
│   │   └── brick-wall.css
│   ├── images
│   │   ├── favicon.ico
│   │   ├── favicon.ico:Zone.Identifier
│   │   └── logo.png
│   ├── js
│   │   └── base.js
│   ├── manifest.json
│   └── sounds
│       ├── hover.mp3
│       └── hover.mp3:Zone.Identifier
├── templates
│   ├── bank
│   │   ├── accounting.html
│   │   ├── bank_list.html
│   │   ├── bank_statement.html
│   │   ├── calendar.html
│   │   ├── other_operations.html
│   │   └── partials
│   │       ├── accounting_table.html
│   │       ├── accounts_table.html
│   │       ├── other_operations_table.html
│   │       └── statement_table.html
│   ├── base.html
│   ├── checker
│   │   ├── check_list.html
│   │   ├── check_print.html
│   │   ├── checker_list.html
│   │   └── partials
│   │       ├── allocation_modal.html
│   │       ├── check_action_modals.html
│   │       ├── checkers_table.html
│   │       ├── checks_table.html
│   │       ├── payment_edit_modal.html
│   │       └── signature_modal.html
│   ├── client
│   │   ├── client_card.html
│   │   ├── client_management.html
│   │   ├── components
│   │   │   ├── client_modal.html
│   │   │   └── entity_modal.html
│   │   └── sale_list.html
│   ├── contract
│   │   ├── contract_list.html
│   │   └── partials
│   │       └── contracts_table.html
│   ├── home.html
│   ├── includes
│   │   └── language_switcher.html
│   ├── invoice
│   │   ├── invoice_confirm_delete.html
│   │   ├── invoice_form.html
│   │   ├── invoice_list.html
│   │   └── partials
│   │       └── invoice_table.html
│   ├── invoices
│   ├── login.html
│   ├── notes
│   │   ├── delivery_note_list.html
│   │   └── reception_note_list.html
│   ├── pay
│   │   ├── accounting.html
│   │   ├── configuration.html
│   │   ├── dashboard.html
│   │   ├── declaration_detail.html
│   │   ├── declarations.html
│   │   ├── items.html
│   │   ├── partials
│   │   │   ├── accounting_table.html
│   │   │   ├── config_form.html
│   │   │   ├── declarations_table.html
│   │   │   └── items_table.html
│   │   └── pending.html
│   ├── presentation
│   │   ├── available_receipts.html
│   │   ├── partials
│   │   │   └── presentations_table.html
│   │   ├── presentation_detail_modal.html
│   │   └── presentation_list.html
│   ├── product
│   │   ├── product_confirm_delete.html
│   │   ├── product_form.html
│   │   └── product_list.html
│   ├── profile.html
│   ├── receipt
│   │   ├── partials
│   │   │   ├── cash_list.html
│   │   │   ├── checks_list.html
│   │   │   ├── compensation_status.html
│   │   │   ├── compensation_timeline_modal.html
│   │   │   ├── lcns_list.html
│   │   │   └── transfers_list.html
│   │   ├── receipt_form_modal.html
│   │   ├── receipt_list.html
│   │   └── receipt_timeline_modal.html
│   ├── supplier
│   │   ├── supplier_confirm_delete.html
│   │   ├── supplier_detail.html
│   │   ├── supplier_form.html
│   │   └── supplier_list.html
│   ├── unauthorized.html
│   ├── users
│   │   └── user_management.html
│   └── vat
│       ├── declaration_detail.html
│       ├── partials
│       │   └── declaration_list.html
│       ├── vat_deduction_details.html
│       └── vat_list.html
├── templatetags
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-38.pyc
│   │   ├── accounting_filters.cpython-38.pyc
│   │   ├── check_tags.cpython-38.pyc
│   │   ├── custom_filters.cpython-38.pyc
│   │   ├── custom_tags.cpython-38.pyc
│   │   ├── permission_tags.cpython-38.pyc
│   │   ├── presentation_filters.cpython-38.pyc
│   │   ├── receipt_filters.cpython-38.pyc
│   │   ├── status_badge.cpython-38.pyc
│   │   └── status_filters.cpython-38.pyc
│   ├── accounting_filters.py
│   ├── check_tags.py
│   ├── custom_filters.py
│   ├── custom_tags.py
│   ├── permission_tags.py
│   ├── presentation_filters.py
│   ├── receipt_filters.py
│   └── status_filters.py
├── tests.py
├── urls.py
├── utils.py
├── views.py
├── views_auth.py
├── views_bank.py
├── views_checkers.py
├── views_client.py
├── views_contract.py
├── views_credit_notes.py
├── views_entity.py
├── views_invoice.py
├── views_notes.py
├── views_pay.py
├── views_presentation.py
├── views_product.py
├── views_production.py
├── views_receipts.py
├── views_statement.py
├── views_supplier.py
├── views_transfer.py
├── views_users.py
└── views_vat.py

41 directories, 277 files
