from django import forms
from django.core.exceptions import ValidationError
from .models import (DeliveryNote, Invoice, InvoiceProduct, Product, CheckReceipt, LCN, CashReceipt, ReceptionNote, Supplier, TransferReceipt, 
    Presentation, PresentationReceipt, MOROCCAN_BANKS)
from django.forms.models import inlineformset_factory
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
import re


class SupplierCreateForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 
            'accounting_code', 'is_energy', 'service', 'delay_convention', 
            'is_regulated', 'regulation_file_path'
        ]

    def clean_ice_code(self):
        ice_code = self.cleaned_data.get('ice_code')
        if len(ice_code) != 15:
            raise ValidationError("ICE code must be exactly 15 digits.")
        return ice_code

    def clean_delay_convention(self):
        delay_convention = self.cleaned_data.get('delay_convention')
        valid_values = [0, 30, 60, 90, 120]
        if delay_convention not in valid_values:
            raise ValidationError("Delay convention must be 0, 30, 60, 90, or 120.")
        return delay_convention
    
    
# Define the inline formset for linking Invoice and InvoiceProduct
InvoiceProductFormset = inlineformset_factory(
    Invoice,
    InvoiceProduct,
    fields=['product', 'quantity', 'unit_price', 'reduction_rate', 'vat_rate'],
    extra=1,  # Number of empty forms to display initially
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01'}),
        'reduction_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        'vat_rate': forms.Select(attrs={'class': 'form-control'}),
    }
)

class InvoiceCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        print("INITIALIZING CREATE FORM")
        super().__init__(*args, **kwargs)
        print(f"CREATE FORM fields: {self.fields}")

        self.fields['document'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'application/pdf'
        })

    class Meta:
        model = Invoice
        fields = [
            'ref', 'date', 'supplier',
            'invoice_type', 'doc_status',
            'document', 'cash_payment_allowed'
        ]
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-control'}),
            'doc_status': forms.Select(attrs={'class': 'form-control'}),
            'cash_payment_allowed': forms.CheckboxInput(attrs={
                'class': 'custom-control-input',
                'data-toggle': 'tooltip',
                'title': 'Enable cash payment for this invoice'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('cash_payment_allowed') and cleaned_data.get('total_amount', 0) > 5000:
            raise ValidationError("Invoices over 5000 cannot be paid by cash")
        return cleaned_data

class InvoiceUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Format the date for HTML5 date input
        if self.instance and self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')
        
        self.fields['supplier'].disabled = True

    class Meta:
        model = Invoice
        fields = [
            'ref', 'date', 'supplier',
            'invoice_type', 'doc_status',
            'document', 'cash_payment_allowed'
        ]
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'format': '%Y-%m-%d'  # Add explicit format
            }),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-control'}),
            'doc_status': forms.Select(attrs={'class': 'form-control'}),
            'cash_payment_allowed': forms.CheckboxInput(attrs={
                'class': 'custom-control-input',
                'data-toggle': 'tooltip',
                'title': 'Enable cash payment for this invoice'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['supplier'] = self.instance.supplier
        return cleaned_data

class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = ['ref', 'date', 'supplier', 'amount', 'document', 'notes']
        widgets = {
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'application/pdf'
        })

class ReceptionNoteForm(forms.ModelForm):
    class Meta:
        model = ReceptionNote
        fields = ['ref', 'date', 'supplier', 'amount', 'document', 'notes']
        widgets = {
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'application/pdf'
        })

class ProductForm(forms.ModelForm):
    vat_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.Select(choices=[
            (Decimal('0.00'), '0%'),
            (Decimal('7.00'), '7%'), 
            (Decimal('10.00'), '10%'),
            (Decimal('11.00'), '11%'),
            (Decimal('14.00'), '14%'),
            (Decimal('16.00'), '16%'),
            (Decimal('20.00'), '20%')
        ])
    )

    class Meta:
        model = Product
        fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 
                 'fiscal_label', 'is_asset', 'asset_account']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input asset-toggle'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        # Hide expense_code field as it will be set automatically for assets
        self.fields['expense_code'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        is_asset = cleaned_data.get('is_asset')
        asset_account = cleaned_data.get('asset_account')
        
        if is_asset:
            if not asset_account:
                self.add_error('asset_account', _('Asset account is required for assets'))
            else:
                # Set expense_code to asset account code
                cleaned_data['expense_code'] = asset_account.account_code
                # Validate 4-digit minimum for asset account code
                if not re.match(r'^[0-9]{4,}$', str(asset_account.account_code)):
                    self.add_error('asset_account', _("Asset account code must be numeric and at least 4 characters long."))
                self.errors.pop('expense_code', None)
        else:
            # For non-assets, validate expense_code
            expense_code = cleaned_data.get('expense_code')
            if not expense_code:
                self.add_error('expense_code', _('Expense code is required for non-assets'))
            elif not re.match(r'^[0-9]{5,}$', str(expense_code)):
                self.add_error('expense_code', _('Expense code must be numeric and at least 5 characters long.'))
            cleaned_data['asset_account'] = None

        return cleaned_data

    def clean_vat_rate(self):
        vat_rate = self.cleaned_data.get('vat_rate')
        print(f"\n=== Clean VAT Rate: {vat_rate} ===")
        if vat_rate:
            return Decimal(str(vat_rate))
        return vat_rate

    def clean_name(self):
        name = self.cleaned_data.get('name')
        is_asset = self.data.get('is_asset') == 'on'
        
        # Check for existing product with same name (case insensitive)
        existing_product = Product.objects.filter(
            name__iexact=name,
            is_asset=is_asset
        ).exclude(pk=self.instance.pk if self.instance else None).exists()
        
        if existing_product:
            raise ValidationError(
                _('A %(type)s with this name already exists.') % {
                    'type': _('asset') if is_asset else _('product')
                }
            )
        return name

class CheckReceiptForm(forms.ModelForm):
    class Meta:
        model = CheckReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month',
            'due_date', 'check_number', 'issuing_bank', 'branch',
            'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'issuing_bank': forms.Select(choices=MOROCCAN_BANKS)
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit compensates to rejected, uncompensated checks
        self.fields['compensates'].queryset = CheckReceipt.objects.filter(
            status=CheckReceipt.STATUS_REJECTED
        ).exclude(
            status=CheckReceipt.STATUS_COMPENSATED
        )

class LCNForm(forms.ModelForm):
    class Meta:
        model = LCN
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month',
            'due_date', 'lcn_number', 'issuing_bank',
            'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'issuing_bank': forms.Select(choices=MOROCCAN_BANKS)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit compensates to rejected, uncompensated LCNs
        self.fields['compensates'].queryset = LCN.objects.filter(
            status=LCN.STATUS_REJECTED
        ).exclude(
            status=LCN.STATUS_COMPENSATED
        )

class CashReceiptForm(forms.ModelForm):
    class Meta:
        model = CashReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'reference_number', 'credited_account', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TransferReceiptForm(forms.ModelForm):
    class Meta:
        model = TransferReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'transfer_reference', 'credited_account', 
            'transfer_date', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'transfer_date': forms.DateInput(attrs={'type': 'date'}),
        }