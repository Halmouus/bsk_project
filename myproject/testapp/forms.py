from django import forms
from django.core.exceptions import ValidationError
from .models import (DeliveryNote, Invoice, InvoiceProduct, Product, CheckReceipt, LCN, CashReceipt, ReceptionNote, Supplier, TransferReceipt, 
    Presentation, PresentationReceipt, MOROCCAN_BANKS)
from django.forms.models import inlineformset_factory
from decimal import Decimal


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

        # Initialize document fields
        self.fields['document'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'application/pdf'
        })

    class Meta:
        model = Invoice
        fields = [
            'ref', 'date', 'supplier',
            'invoice_type', 'doc_status',
            'document'
        ]
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            # New widgets
            'invoice_type': forms.Select(attrs={'class': 'form-control'}),
            'doc_status': forms.Select(attrs={'class': 'form-control'}),
        }

class InvoiceUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        print("INITIALIZING UPDATE FORM")
        super().__init__(*args, **kwargs)
        print(f"UPDATE FORM Before disable: {self.fields}")
        self.fields['supplier'].disabled = True
        print(f"UPDATE FORM After disable: {self.fields}")

    class Meta:
        model = Invoice
        fields = [
            'ref', 'date', 'supplier',
            'invoice_type', 'doc_status',
            'document'
        ]
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            # New widgets
            'invoice_type': forms.Select(attrs={'class': 'form-control'}),
            'doc_status': forms.Select(attrs={'class': 'form-control'}),
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
    class Meta:
        model = Product
        fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
        widgets = {
            'vat_rate': forms.Select(choices=[
                ('0.00', '0%'), 
                ('7.00', '7%'), 
                ('10.00', '10%'), 
                ('11.00', '11%'), 
                ('14.00', '14%'), 
                ('16.00', '16%'), 
                ('20.00', '20%')
            ])
        }

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