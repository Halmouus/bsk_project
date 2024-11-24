from django import forms
from .models import Invoice, InvoiceProduct, Product
from django.forms.models import inlineformset_factory
from decimal import Decimal

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
        print("INITIALIZING CREATE FORM")  # Debug print
        super().__init__(*args, **kwargs)
        print(f"CREATE FORM fields: {self.fields}")  # Debug print

    class Meta:
        model = Invoice
        fields = ['ref', 'date', 'supplier']
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

class InvoiceUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        print("INITIALIZING UPDATE FORM")  # Debug print
        super().__init__(*args, **kwargs)
        print(f"UPDATE FORM Before disable: {self.fields}")  # Debug print
        self.fields['supplier'].disabled = True
        print(f"UPDATE FORM After disable: {self.fields}")  # Debug print

    class Meta:
        model = Invoice
        fields = ['ref', 'date', 'supplier']
        widgets = { 
            'ref': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['supplier'] = self.instance.supplier
        return cleaned_data
        

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