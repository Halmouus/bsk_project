.
├── __init__.py
├── __pycache__
│   ├── __init__.cpython-38.pyc
│   ├── admin.cpython-38.pyc
│   ├── apps.cpython-38.pyc
│   ├── base.cpython-38.pyc
│   ├── forms.cpython-38.pyc
│   ├── middleware.cpython-38.pyc
│   ├── models.cpython-38.pyc
│   ├── signals.cpython-38.pyc
│   ├── urls.cpython-38.pyc
│   ├── views.cpython-38.pyc
│   ├── views_bank.cpython-38.pyc
│   ├── views_checkers.cpython-38.pyc
│   ├── views_client.cpython-38.pyc
│   ├── views_credit_notes.cpython-38.pyc
│   ├── views_entity.cpython-38.pyc
│   ├── views_invoice.cpython-38.pyc
│   ├── views_presentation.cpython-38.pyc
│   ├── views_product.cpython-38.pyc
│   ├── views_receipts.cpython-38.pyc
│   ├── views_statement.cpython-38.pyc
│   ├── views_supplier.cpython-38.pyc
│   └── views_transfer.cpython-38.pyc
├── admin.py
├── apps.py
├── base.py
├── codebase.md
├── file_structure.md
├── forms.py
├── management
│   ├── __init__.py
│   ├── __pycache__
│   │   └── __init__.cpython-38.pyc
│   └── commands
│       ├── __init__.py
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
│   ├── __init__.py
│   └── __pycache__
│       ├── 0001_initial.cpython-38.pyc
│       ├── 0002_cashreceipt_compensating_content_type_and_more.cpython-38.pyc
│       ├── 0002_check_rejected_at.cpython-38.pyc
│       ├── 0002_checker_position_signatures.cpython-38.pyc
│       ├── 0002_client_entity.cpython-38.pyc
│       ├── 0002_make_bank_account_nullable.cpython-38.pyc
│       ├── 0002_remove_invoice_unique_supplier_invoice_ref_and_more.cpython-38.pyc
│       ├── 0003_accountingentry_bankstatement.cpython-38.pyc
│       ├── 0003_alter_check_position.cpython-38.pyc
│       ├── 0003_check_received_at_check_received_notes.cpython-38.pyc
│       ├── 0003_client_client_code_alter_entity_accounting_code_and_more.cpython-38.pyc
│       ├── 0003_clientsale_sale_type_alter_clientsale_amount_and_more.cpython-38.pyc
│       ├── 0004_alter_client_options_alter_entity_options_and_more.cpython-38.pyc
│       ├── 0004_check_signatures_alter_check_status.cpython-38.pyc
│       ├── 0004_interbanktransfer_transferredrecord.cpython-38.pyc
│       ├── 0004_presentationreceipt_presentation_status_and_more.cpython-38.pyc
│       ├── 0005_alter_check_status.cpython-38.pyc
│       ├── 0005_bankfeetype_bankfeetransaction.cpython-38.pyc
│       ├── 0005_checkreceipt_lcn_presentation_transferreceipt_and_more.cpython-38.pyc
│       ├── 0005_remove_presentationreceipt_presentation_status_and_more.cpython-38.pyc
│       ├── 0006_bankfeetype_created_at_bankfeetype_updated_at_and_more.cpython-38.pyc
│       ├── 0006_check_printed_at_check_signed_at.cpython-38.pyc
│       ├── 0006_clientsale.cpython-38.pyc
│       ├── 0006_presentationreceipt_rejection_cause_and_more.cpython-38.pyc
│       ├── 0007_check_position_signatures.cpython-38.pyc
│       ├── 0007_checkreceipt_unpaid_date_lcn_unpaid_date.cpython-38.pyc
│       ├── 0007_presentation_bank_reference_presentation_document_and_more.cpython-38.pyc
│       ├── 0007_remove_presentationreceipt_rejection_cause_and_more.cpython-38.pyc
│       ├── 0008_alter_receipthistory_options_and_more.cpython-38.pyc
│       ├── 0008_bankaccount_bank_overdraft_and_more.cpython-38.pyc
│       ├── 0008_remove_check_position_signatures_and_more.cpython-38.pyc
│       ├── 0008_remove_checkreceipt_bank_name_and_more.cpython-38.pyc
│       ├── 0009_alter_checkreceipt_check_number_alter_lcn_lcn_number_and_more.cpython-38.pyc
│       ├── 0009_checkreceipt_compensating_content_type_and_more.cpython-38.pyc
│       ├── 0009_remove_bankaccount_bank_overdraft_and_more.cpython-38.pyc
│       ├── 0010_receipthistory.cpython-38.pyc
│       ├── 0010_remove_invoice_unique_supplier_invoice_ref_and_more.cpython-38.pyc
│       ├── 0011_merge_20241209_2104.cpython-38.pyc
│       ├── 0011_presentationreceipt_status_and_more.cpython-38.pyc
│       ├── 0012_remove_presentationreceipt_status.cpython-38.pyc
│       ├── 0013_presentation_locked.cpython-38.pyc
│       ├── 0014_remove_presentation_locked.cpython-38.pyc
│       └── __init__.cpython-38.pyc
├── models.py
├── services.py
├── signals.py
├── templates
│   ├── bank
│   │   ├── accounting.html
│   │   ├── bank_list.html
│   │   ├── bank_statement.html
│   │   ├── other_operations.html
│   │   └── partials
│   ├── base.html
│   ├── checker
│   │   ├── check_list.html
│   │   ├── checker_list.html
│   │   └── partials
│   ├── client
│   │   ├── client_card.html
│   │   ├── client_management.html
│   │   ├── components
│   │   └── sale_list.html
│   ├── home.html
│   ├── invoice
│   │   ├── invoice_confirm_delete.html
│   │   ├── invoice_form.html
│   │   ├── invoice_list.html
│   │   └── partials
│   ├── login.html
│   ├── presentation
│   │   ├── available_receipts.html
│   │   ├── partials
│   │   ├── presentation_detail_modal.html
│   │   └── presentation_list.html
│   ├── product
│   │   ├── product_confirm_delete.html
│   │   ├── product_form.html
│   │   └── product_list.html
│   ├── profile.html
│   ├── receipt
│   │   ├── partials
│   │   ├── receipt_form_modal.html
│   │   ├── receipt_list.html
│   │   └── receipt_timeline_modal.html
│   └── supplier
│       ├── supplier_confirm_delete.html
│       ├── supplier_form.html
│       └── supplier_list.html
├── templatetags
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-38.pyc
│   │   ├── accounting_filters.cpython-38.pyc
│   │   ├── check_tags.cpython-38.pyc
│   │   ├── custom_filters.cpython-38.pyc
│   │   ├── presentation_filters.cpython-38.pyc
│   │   ├── receipt_filters.cpython-38.pyc
│   │   ├── status_badge.cpython-38.pyc
│   │   └── status_filters.cpython-38.pyc
│   ├── accounting_filters.py
│   ├── check_tags.py
│   ├── custom_filters.py
│   ├── presentation_filters.py
│   ├── receipt_filters.py
│   └── status_filters.py
├── tests.py
├── urls.py
├── views.py
├── views_bank.py
├── views_checkers.py
├── views_client.py
├── views_credit_notes.py
├── views_entity.py
├── views_invoice.py
├── views_presentation.py
├── views_product.py
├── views_receipts.py
├── views_statement.py
├── views_supplier.py
└── views_transfer.py

23 directories, 149 files
