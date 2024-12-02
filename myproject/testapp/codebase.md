# __init__.py

```py
default_app_config = 'testapp.apps.TestappConfig'

```

# admin.py

```py
from django.contrib import admin

```

# apps.py

```py
from django.apps import AppConfig


class TestappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testapp'

    def ready(self):
        import testapp.signals

```

# base.py

```py
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

```

# forms.py

```py
from django import forms
from django.core.exceptions import ValidationError
from .models import (Invoice, InvoiceProduct, Product, CheckReceipt, LCN, CashReceipt, TransferReceipt, 
    Presentation, PresentationReceipt)
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

class CheckReceiptForm(forms.ModelForm):
    class Meta:
        model = CheckReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'due_date', 'check_number', 'bank_name', 'branch',
            'compensates', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit compensates to rejected, uncompensated checks
        self.fields['compensates'].queryset = Check.objects.filter(
            status=Check.STATUS_REJECTED
        ).exclude(
            status=Check.STATUS_COMPENSATED
        )

class LCNForm(forms.ModelForm):
    class Meta:
        model = LCN
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'due_date', 'lcn_number', 'issuing_bank',
            'compensates', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
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
```

# management/__init__.py

```py

```

# management/commands/__init__.py

```py

```

# management/commands/populate_sample_data.py

```py
# management/commands/populate_sample_data.py

from django.core.management.base import BaseCommand
from testapp.models import BankAccount, Checker
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populates database with sample data'

    def handle(self, *args, **kwargs):
        # Create sample bank accounts
        banks = [
            ('ATW', 'Casablanca'),
            ('BCP', 'Rabat'),
            ('BOA', 'Marrakech'),
            ('CIH', 'Tangier')
        ]
        
        for bank, city in banks:
            # Create national account
            BankAccount.objects.create(
                bank=bank,
                account_number=f"{random.randint(1000000000, 9999999999)}",
                accounting_number=f"{random.randint(10000, 99999)}",
                journal_number=f"{random.randint(10, 99)}",
                city=city,
                account_type='national'
            )
            
            # Create international account
            BankAccount.objects.create(
                bank=bank,
                account_number=f"{random.randint(1000000000, 9999999999)}",
                accounting_number=f"{random.randint(10000, 99999)}",
                journal_number=f"{random.randint(10, 99)}",
                city=city,
                account_type='international'
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated sample data'))
```

# management/commands/reset_app.py

```py
# management/commands/reset_app.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Resets the application data and migrations'

    def handle(self, *args, **kwargs):
        # Get all models from our app
        app_models = apps.get_app_config('testapp').get_models()
        
        with connection.cursor() as cursor:
            # Disable foreign key checks
            if connection.vendor == 'mysql':
                cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
            
            # Drop all tables
            for model in app_models:
                table_name = model._meta.db_table
                self.stdout.write(f'Dropping table {table_name}')
                cursor.execute(f'DROP TABLE IF EXISTS {table_name} CASCADE;')
            
            # Re-enable foreign key checks
            if connection.vendor == 'mysql':
                cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')

        self.stdout.write(self.style.SUCCESS('Successfully reset database'))
```

# middleware.py

```py
from django.shortcuts import redirect

class RedirectIfNotLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is not authenticated and is trying to access profile
        if not request.user.is_authenticated and request.path == '/profile/':
            return redirect('login')  # Redirect to login page

        # Otherwise, proceed as normal
        response = self.get_response(request)
        return response

```

# migrations/__init__.py

```py

```

# migrations/0001_initial.py

```py
# Generated by Django 4.2.16 on 2024-11-29 19:06

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank', models.CharField(choices=[('ATW', 'Attijariwafa Bank'), ('BCP', 'Banque Populaire'), ('BOA', 'Bank of Africa'), ('CAM', 'Crédit Agricole du Maroc'), ('CIH', 'CIH Bank'), ('BMCI', 'BMCI'), ('SGM', 'Société Générale Maroc'), ('CDM', 'Crédit du Maroc'), ('ABB', 'Al Barid Bank'), ('CFG', 'CFG Bank'), ('ABM', 'Arab Bank Maroc'), ('CTB', 'Citibank Maghreb')], max_length=4)),
                ('account_number', models.CharField(max_length=30, validators=[django.core.validators.MinLengthValidator(10, 'Account number must be at least 10 characters'), django.core.validators.RegexValidator('^\\d+$', 'Only numeric characters allowed')])),
                ('accounting_number', models.CharField(max_length=10, validators=[django.core.validators.MinLengthValidator(5, 'Accounting number must be at least 5 characters'), django.core.validators.RegexValidator('^\\d+$', 'Only numeric characters allowed')])),
                ('journal_number', models.CharField(max_length=2, validators=[django.core.validators.RegexValidator('^\\d{2}$', 'Must be exactly 2 digits')])),
                ('city', models.CharField(max_length=100)),
                ('account_type', models.CharField(choices=[('national', 'National'), ('international', 'International')], max_length=15)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['bank', 'account_number'],
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('position', models.CharField(max_length=10, unique=True)),
                ('creation_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_due', models.DateField(blank=True, null=True)),
                ('amount_due', models.DecimalField(decimal_places=2, editable=False, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('observation', models.TextField(blank=True)),
                ('delivered', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancellation_reason', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('printed', 'Printed'), ('ready_to_sign', 'Ready to Sign'), ('pending', 'Pending'), ('delivered', 'Delivered'), ('paid', 'Paid'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('rejected_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.CharField(blank=True, choices=[('insufficient_funds', 'Insufficient Funds'), ('signature_mismatch', 'Signature Mismatch'), ('amount_error', 'Amount Error'), ('date_error', 'Date Error'), ('other', 'Other')], max_length=50, null=True)),
                ('rejection_note', models.TextField(blank=True)),
                ('rejection_date', models.DateTimeField(blank=True, null=True)),
                ('received_at', models.DateTimeField(blank=True, null=True)),
                ('received_notes', models.TextField(blank=True)),
                ('signatures', models.JSONField(default=list)),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
        migrations.CreateModel(
            name='Checker',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(blank=True, max_length=10, unique=True)),
                ('type', models.CharField(choices=[('CHQ', 'Cheque'), ('LCN', 'LCN')], max_length=3)),
                ('num_pages', models.IntegerField(choices=[(25, '25'), (50, '50'), (100, '100')])),
                ('index', models.CharField(max_length=3, validators=[django.core.validators.RegexValidator('^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')])),
                ('starting_page', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('final_page', models.IntegerField(blank=True)),
                ('current_position', models.IntegerField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('owner', models.CharField(default='Briqueterie Sidi Kacem', max_length=100)),
                ('status', models.CharField(choices=[('new', 'New'), ('in_use', 'In Use'), ('completed', 'Completed')], default='new', max_length=10)),
                ('position_signatures', models.JSONField(default=dict)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExportRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exported_at', models.DateTimeField(auto_now_add=True)),
                ('filename', models.CharField(max_length=255)),
                ('note', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ref', models.CharField(max_length=50, unique=True)),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft', max_length=20)),
                ('payment_due_date', models.DateField(blank=True, null=True)),
                ('exported_at', models.DateTimeField(blank=True, null=True)),
                ('payment_status', models.CharField(choices=[('not_paid', 'Not Paid'), ('partially_paid', 'Partially Paid'), ('paid', 'Paid')], default='not_paid', max_length=20)),
                ('type', models.CharField(choices=[('invoice', 'Invoice'), ('credit_note', 'Credit Note')], default='invoice', max_length=20)),
            ],
            options={
                'permissions': [('can_export_invoice', 'Can export invoice'), ('can_unexport_invoice', 'Can unexport invoice')],
            },
        ),
        migrations.CreateModel(
            name='InvoiceProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('reduction_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('vat_rate', models.DecimalField(choices=[(0.0, '0%'), (7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='item',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('vat_rate', models.DecimalField(choices=[(0.0, '0%'), (7.0, '7%'), (10.0, '10%'), (11.0, '11%'), (14.0, '14%'), (16.0, '16%'), (20.0, '20%')], decimal_places=2, default=20.0, max_digits=5)),
                ('expense_code', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])),
                ('is_energy', models.BooleanField(default=False)),
                ('fiscal_label', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('position', models.CharField(max_length=100)),
                ('date_of_joining', models.DateField(blank=True, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('contact_number', models.CharField(blank=True, max_length=15)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')])),
                ('if_code', models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')])),
                ('ice_code', models.CharField(max_length=15, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')])),
                ('rc_code', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only numeric characters are allowed.')])),
                ('rc_center', models.CharField(max_length=100, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')])),
                ('accounting_code', models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator('^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])),
                ('is_energy', models.BooleanField(default=False)),
                ('service', models.CharField(blank=True, max_length=255, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')])),
                ('delay_convention', models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)),
                ('is_regulated', models.BooleanField(default=False)),
                ('regulation_file_path', models.FileField(blank=True, null=True, upload_to='supplier_regulations/')),
            ],
        ),
        migrations.AddConstraint(
            model_name='supplier',
            constraint=models.UniqueConstraint(fields=('name', 'rc_code'), name='unique_supplier_name_rc_code'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('name', 'expense_code'), name='unique_product_name_expense_code'),
        ),
        migrations.AddField(
            model_name='invoiceproduct',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='testapp.invoice'),
        ),
        migrations.AddField(
            model_name='invoiceproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.product'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='export_history',
            field=models.ManyToManyField(blank=True, related_name='invoices', to='testapp.exportrecord'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='original_invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='credit_notes', to='testapp.invoice'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.supplier'),
        ),
        migrations.AddField(
            model_name='exportrecord',
            name='exported_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='checker',
            name='bank_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount'),
        ),
        migrations.AddField(
            model_name='check',
            name='beneficiary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.supplier'),
        ),
        migrations.AddField(
            model_name='check',
            name='cause',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.invoice'),
        ),
        migrations.AddField(
            model_name='check',
            name='checker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checks', to='testapp.checker'),
        ),
        migrations.AddField(
            model_name='check',
            name='replaces',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='replaced_by', to='testapp.check'),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(fields=('supplier', 'ref'), name='unique_supplier_invoice_ref'),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('original_invoice__isnull', True), ('type', 'invoice')), models.Q(('original_invoice__isnull', False), ('type', 'credit_note')), _connector='OR')), name='credit_note_must_have_original_invoice'),
        ),
        migrations.AddConstraint(
            model_name='check',
            constraint=models.CheckConstraint(check=models.Q(('amount__lte', models.F('amount_due'))), name='check_amount_cannot_exceed_due'),
        ),
    ]

```

# migrations/0002_client_entity.py

```py
# Generated by Django 4.2.16 on 2024-11-30 07:37

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('ice_code', models.CharField(max_length=50, unique=True)),
                ('accounting_code', models.CharField(max_length=50, unique=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={
                'verbose_name_plural': 'entities',
                'ordering': ['name'],
            },
        ),
    ]

```

# migrations/0003_client_client_code_alter_entity_accounting_code_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-30 08:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0002_client_entity'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='client_code',
            field=models.CharField(default=12345, max_length=8, unique=True, validators=[django.core.validators.RegexValidator('^\\d{5,8}$', 'Client code must be numeric and between 5 and 8 digits.')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='entity',
            name='accounting_code',
            field=models.CharField(max_length=7, unique=True, validators=[django.core.validators.RegexValidator(message='Accounting code must start with 3 and be 5-7 digits long', regex='^3\\d{4,6}$')]),
        ),
        migrations.AlterField(
            model_name='entity',
            name='ice_code',
            field=models.CharField(max_length=15, unique=True, validators=[django.core.validators.RegexValidator(message='ICE code must be exactly 15 digits', regex='^\\d{15}$')]),
        ),
    ]

```

# migrations/0004_alter_client_options_alter_entity_options_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-30 10:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0003_client_client_code_alter_entity_accounting_code_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ['name'], 'verbose_name': 'Client', 'verbose_name_plural': 'Clients'},
        ),
        migrations.AlterModelOptions(
            name='entity',
            options={'ordering': ['name'], 'verbose_name': 'Entity', 'verbose_name_plural': 'Entities'},
        ),
        migrations.AlterField(
            model_name='client',
            name='client_code',
            field=models.CharField(help_text='Enter a unique 5-10 digit code', max_length=10, unique=True, validators=[django.core.validators.MinLengthValidator(5, 'Client code must be at least 5 digits'), django.core.validators.MaxLengthValidator(10, 'Client code cannot exceed 10 digits'), django.core.validators.RegexValidator(message='Client code must contain only digits', regex='^\\d+$')]),
        ),
        migrations.AlterField(
            model_name='client',
            name='name',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(message='Name can only contain letters and spaces', regex='^[a-zA-Z\\s]*$')]),
        ),
        migrations.AlterField(
            model_name='entity',
            name='accounting_code',
            field=models.CharField(help_text='Enter 5-7 digits starting with 3', max_length=7, unique=True, validators=[django.core.validators.RegexValidator(message='Accounting code must start with 3 and be 5-7 digits long', regex='^3\\d{4,6}$')]),
        ),
        migrations.AlterField(
            model_name='entity',
            name='ice_code',
            field=models.CharField(help_text='Enter exactly 15 digits', max_length=15, unique=True, validators=[django.core.validators.RegexValidator(message='ICE code must be exactly 15 digits', regex='^\\d{15}$')]),
        ),
        migrations.AlterField(
            model_name='entity',
            name='name',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(message='Name can only contain letters and spaces', regex='^[a-zA-Z\\s]*$')]),
        ),
    ]

```

# migrations/0005_checkreceipt_lcn_presentation_transferreceipt_and_more.py

```py
# Generated by Django 4.2.16 on 2024-11-30 18:39

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0004_alter_client_options_alter_entity_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operation_date', models.DateField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('client_year', models.IntegerField()),
                ('client_month', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('PORTFOLIO', 'In Portfolio'), ('PRESENTED_COLLECTION', 'Presented for Collection'), ('PRESENTED_DISCOUNT', 'Presented for Discount'), ('DISCOUNTED', 'Discounted'), ('PAID', 'Paid'), ('REJECTED', 'Rejected'), ('COMPENSATED', 'Compensated')], default='PORTFOLIO', max_length=20)),
                ('check_number', models.CharField(max_length=50)),
                ('bank_name', models.CharField(max_length=100)),
                ('branch', models.CharField(blank=True, max_length=100)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.client')),
                ('compensates', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compensated_by', to='testapp.checkreceipt')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.entity')),
            ],
            options={
                'verbose_name': 'Check',
                'verbose_name_plural': 'Checks',
            },
        ),
        migrations.CreateModel(
            name='LCN',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operation_date', models.DateField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('client_year', models.IntegerField()),
                ('client_month', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('PORTFOLIO', 'In Portfolio'), ('PRESENTED_COLLECTION', 'Presented for Collection'), ('PRESENTED_DISCOUNT', 'Presented for Discount'), ('DISCOUNTED', 'Discounted'), ('PAID', 'Paid'), ('REJECTED', 'Rejected'), ('COMPENSATED', 'Compensated')], default='PORTFOLIO', max_length=20)),
                ('lcn_number', models.CharField(max_length=50)),
                ('issuing_bank', models.CharField(max_length=100)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.client')),
                ('compensates', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compensated_by', to='testapp.lcn')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.entity')),
            ],
            options={
                'verbose_name': 'LCN',
                'verbose_name_plural': 'LCNs',
            },
        ),
        migrations.CreateModel(
            name='Presentation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('presentation_type', models.CharField(choices=[('COLLECTION', 'Collection'), ('DISCOUNT', 'Discount')], max_length=10)),
                ('date', models.DateField()),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('notes', models.TextField(blank=True)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount')),
            ],
            options={
                'verbose_name': 'Presentation',
                'verbose_name_plural': 'Presentations',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TransferReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operation_date', models.DateField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('client_year', models.IntegerField()),
                ('client_month', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('transfer_reference', models.CharField(max_length=100)),
                ('transfer_date', models.DateField(default=django.utils.timezone.now)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.client')),
                ('credited_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfer_receipts', to='testapp.bankaccount')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.entity')),
            ],
            options={
                'verbose_name': 'Transfer',
                'verbose_name_plural': 'Transfers',
            },
        ),
        migrations.CreateModel(
            name='CashReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operation_date', models.DateField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('client_year', models.IntegerField()),
                ('client_month', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.bankaccount')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.client')),
                ('credited_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cash_receipts', to='testapp.bankaccount')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.entity')),
            ],
            options={
                'verbose_name': 'Cash Receipt',
                'verbose_name_plural': 'Cash Receipts',
            },
        ),
        migrations.CreateModel(
            name='PresentationReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('checkreceipt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='check_presentations', to='testapp.checkreceipt')),
                ('lcn', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lcn_presentations', to='testapp.lcn')),
                ('presentation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presentation_receipts', to='testapp.presentation')),
            ],
            options={
                'verbose_name': 'Presentation Receipt',
                'verbose_name_plural': 'Presentation Receipts',
                'unique_together': {('presentation', 'lcn'), ('presentation', 'checkreceipt')},
            },
        ),
    ]

```

# migrations/0006_clientsale.py

```py
# Generated by Django 4.2.16 on 2024-12-01 13:04

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0005_checkreceipt_lcn_presentation_transferreceipt_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientSale',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.client')),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]

```

# models.py

```py
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, MinLengthValidator, MaxLengthValidator
from .base import BaseModel
from datetime import timedelta
import datetime
import random
import string
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class item(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()    
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Supplier(BaseModel):

    numeric_validator = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')
    alphanumeric_validator = RegexValidator(r'^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')

    name = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    if_code = models.CharField(max_length=20, unique=True, validators=[numeric_validator])
    ice_code = models.CharField(max_length=15, unique=True, validators=[numeric_validator])  # Exactly 15 characters
    rc_code = models.CharField(max_length=20, validators=[numeric_validator])
    rc_center = models.CharField(max_length=100, validators=[alphanumeric_validator])
    accounting_code = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    service = models.CharField(max_length=255, blank=True, validators=[alphanumeric_validator])  # Description of merch/service sold
    delay_convention = models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)
    is_regulated = models.BooleanField(default=False)
    regulation_file_path = models.FileField(upload_to='supplier_regulations/', null=True, blank=True)

    def clean(self):
        super().clean()
        # Ensure IF code is numeric
        if not self.if_code.isdigit():
            raise ValidationError("IF code must be numeric.")
        # Ensure ICE code has exactly 15 characters
        if len(self.ice_code) != 15:
            raise ValidationError("ICE code must contain exactly 15 characters.")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'rc_code'], name='unique_supplier_name_rc_code')
        ]

    def __str__(self):
        return self.name

class Product(BaseModel):
    name = models.CharField(max_length=100)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, choices=[
    (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
])
    expense_code = models.CharField(max_length=20, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    fiscal_label = models.CharField(max_length=255, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'expense_code'], name='unique_product_name_expense_code')
        ]
    def __str__(self):
        return self.name

class Invoice(BaseModel):
    INVOICE_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('credit_note', 'Credit Note'),
    ]
    ref = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft'
    )
    payment_due_date = models.DateField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    export_history = models.ManyToManyField('ExportRecord', blank=True, related_name='invoices')

    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid')
    ]

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_paid'
    )
    
    type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPE_CHOICES,
        default='invoice'
    )

    original_invoice = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='credit_notes'
    )

    def save(self, *args, **kwargs):
        if self.type == 'invoice':  # Only calculate payment_due_date for regular invoices
            if not self.payment_due_date:
                self.payment_due_date = self.date + timedelta(days=self.supplier.delay_convention)
        else:  # For credit notes
            self.payment_due_date = None

        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['supplier', 'ref'], name='unique_supplier_invoice_ref'),
            models.CheckConstraint(
                check=Q(
                    Q(type='invoice', original_invoice__isnull=True) |
                    Q(type='credit_note', original_invoice__isnull=False)
                ),
                name='credit_note_must_have_original_invoice'
            )
        ]
        permissions = [
        ("can_export_invoice", "Can export invoice"),
        ("can_unexport_invoice", "Can unexport invoice"),
        ]

    @property
    def fiscal_label(self):
        """Generate a combined fiscal label from all related products."""
        products = [(item.product.fiscal_label, item.quantity * item.unit_price) 
                    for item in self.products.all()]
        unique_labels = []
        seen = set()
        
        # Sort by value and get unique labels
        for label, _ in sorted(products, key=lambda x: x[1], reverse=True):
            if label not in seen:
                unique_labels.append(label)
                seen.add(label)
        
        top_labels = unique_labels[:3]
        if len(unique_labels) > 3:
            top_labels.append('...')
        
        return " - ".join(top_labels)
    
    @property
    def raw_amount(self):
        """Calculate the total amount before tax, considering reduction rate for each product."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100))
                for item in self.products.all()
            ]
        )

    @property
    def total_tax_amount(self):
        """Calculate the total tax amount for the invoice considering different VAT rates."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100) * item.vat_rate / 100)
                for item in self.products.all()
            ]
        )

    @property
    def total_amount(self):
        """Calculate the total amount of the invoice including tax."""
        return self.raw_amount + self.total_tax_amount
    
    @property
    def net_amount(self):
        """Calculate net amount after credit notes"""
        credit_notes_total = sum(
            cn.total_amount for cn in self.credit_notes.all()
        )
        return self.total_amount - credit_notes_total

    @property
    def has_credit_notes(self):
        """Check if invoice has any credit notes"""
        return self.credit_notes.exists()
    
    @property
    def can_be_credited(self):
        """Check if invoice can have more credit notes"""
        if self.type == 'credit_note':
            return False
        if self.payment_status == 'paid':
            return False
        credit_notes_total = sum(cn.total_amount for cn in self.credit_notes.all())
        return credit_notes_total < self.total_amount
    

    def clean(self):
        """Custom clean method to validate credit notes"""
        super().clean()
        if self.type == 'credit_note':
            if not self.original_invoice:
                raise ValidationError("Credit note must reference an original invoice")
            if self.original_invoice.type != 'invoice':
                raise ValidationError("Cannot create credit note for another credit note")
            if self.supplier != self.original_invoice.supplier:
                raise ValidationError("Credit note must have same supplier as original invoice")

    def get_credited_quantities(self):
        """Get total credited quantities per product"""
        credited_quantities = {}
        for credit_note in self.credit_notes.all():
            for item in credit_note.products.all():
                if item.product_id in credited_quantities:
                    credited_quantities[item.product_id] += item.quantity
                else:
                    credited_quantities[item.product_id] = item.quantity
        return credited_quantities

    def get_available_quantities(self):
        """Get available quantities that can still be credited"""
        original_quantities = {
            item.product_id: item.quantity 
            for item in self.products.all()
        }
        credited_quantities = self.get_credited_quantities()
        
        return {
            product_id: original_quantities[product_id] - credited_quantities.get(product_id, 0)
            for product_id in original_quantities
        }

    def get_accounting_entries(self):
        entries = []
        sign = -1 if self.type == 'credit_note' else 1
        expense_groups = {}
        tax_groups = {}
        
        for invoice_product in self.products.all():
            # Group products by expense code
            key = invoice_product.product.expense_code
            if key not in expense_groups:
                expense_groups[key] = {
                    'products': {},  # Changed to dict to track values
                    'amount': 0,
                    'is_energy': invoice_product.product.is_energy
                }
            # Track product value
            product_value = (
                invoice_product.quantity * 
                invoice_product.unit_price * 
                (1 - invoice_product.reduction_rate / 100) * 
                sign
            )
            expense_groups[key]['products'][invoice_product.product.name] = product_value
            expense_groups[key]['amount'] += product_value

            # Group taxes by rate (unchanged)
            tax_key = invoice_product.vat_rate
            if tax_key not in tax_groups:
                tax_groups[tax_key] = 0
            tax_groups[tax_key] += (product_value * invoice_product.vat_rate / 100)

        # Add expense entries with top 3 products by value
        prefix = "CN -" if self.type == 'credit_note' else ""
        for expense_code, data in expense_groups.items():
            # Sort products by value and get unique names
            sorted_products = sorted(data['products'].items(), key=lambda x: x[1], reverse=True)
            unique_products = []
            seen = set()
            for name, _ in sorted_products:
                if name not in seen:
                    unique_products.append(name)
                    seen.add(name)
            
            product_names = unique_products[:3]
            if len(sorted_products) > 3:
                product_names.append('...')

            entries.append({
                'date': self.date,
                'label': f"{prefix} {', '.join(product_names)}",
                'debit': data['amount'] if sign > 0 else None,
                'credit': abs(data['amount']) if sign < 0 else None,
                'account_code': expense_code,
                'reference': self.ref,
                'journal': '10' if data['is_energy'] else '01',
                'counterpart': ''
            })

        # Rest of the method remains unchanged
        for rate, amount in tax_groups.items():
            if rate > 0:
                entries.append({
                    'date': self.date,
                    'label': f'VAT {int(rate)}%',
                    'debit': amount if sign > 0 else None,
                    'credit': abs(amount) if sign < 0 else None,
                    'account_code': f'345{int(rate):02d}',
                    'reference': self.ref,
                    'journal': '10' if self.supplier.is_energy else '01',
                    'counterpart': ''
                })

        entries.append({
            'date': self.date,
            'label': self.supplier.name,
            'debit': abs(self.total_amount) if sign < 0 else None,
            'credit': self.total_amount if sign > 0 else None,
            'account_code': self.supplier.accounting_code,
            'reference': self.ref,
            'journal': '10' if self.supplier.is_energy else '01',
            'counterpart': ''
        })

        return entries    
    
    @property
    def amount_available_for_payment(self):
        """Calculate amount available for payment considering credit notes"""
        net_amount = self.net_amount
        payments_sum = sum(
            check.amount 
            for check in Check.objects.filter(
                cause=self
            ).exclude(
                status='cancelled'
            )
        )
        return max(0, net_amount - payments_sum)
    
    def get_payment_details(self):
        """Calculate comprehensive payment details"""
        # Get all non-cancelled checks for this invoice
        valid_checks = Check.objects.filter(
            cause=self
        ).exclude(
            status='cancelled'
        )

        # Calculate various payment amounts
        pending_amount = sum(c.amount for c in valid_checks.filter(status='pending'))
        delivered_amount = sum(c.amount for c in valid_checks.filter(status='delivered'))
        paid_amount = sum(c.amount for c in valid_checks.filter(status='paid'))
        total_issued = sum(c.amount for c in valid_checks)

        # Use net_amount instead of total_amount
        net_amount = self.net_amount
        amount_to_issue = net_amount - total_issued
        remaining_to_pay = net_amount - paid_amount
        payment_percentage = (paid_amount / net_amount * 100) if net_amount else 0

        # Calculate remaining and percentages
        amount_to_issue = self.net_amount - total_issued
        print(f"Amount to issue: {amount_to_issue}")  # Debug output
        remaining_to_pay = self.net_amount - paid_amount
        print(f"Remaining to pay: {remaining_to_pay}") # Debug output
        payment_percentage = (paid_amount / self.net_amount * 100) if self.net_amount else 0
        print(f"Payment percentage: {payment_percentage}") # Debug output

        details = {
            'total_amount': float(self.net_amount),
            'pending_amount': float(pending_amount),
            'delivered_amount': float(delivered_amount),
            'paid_amount': float(paid_amount),
            'amount_to_issue': float(amount_to_issue),
            'remaining_to_pay': float(remaining_to_pay),
            'payment_percentage': float(payment_percentage),
            'payment_status': self.get_payment_status(paid_amount)
        }

        print(details)  # Debug output
        return details

    def get_payment_status(self, paid_amount=None):
        """Determine payment status based on paid amount"""
        if paid_amount is None:
            paid_amount = sum(c.amount for c in Check.objects.filter(
                cause=self, 
                status='paid'
            ).exclude(status='cancelled'))

        if paid_amount >= self.total_amount:
            return 'paid'
        elif paid_amount > 0:
            return 'partially_paid'
        return 'not_paid'


    @property
    def payments_summary(self):
        payments = Check.objects.filter(cause=self).exclude(status='cancelled')
        return {
            'pending_amount': sum(p.amount for p in payments.filter(status='pending')),
            'delivered_amount': sum(p.amount for p in payments.filter(status='delivered')),
            'paid_amount': sum(p.amount for p in payments.filter(status='paid')),
            'percentage_paid': (sum(p.amount for p in payments.filter(status='paid')) / self.total_amount * 100) if self.total_amount else 0,
            'remaining_amount': self.total_amount - sum(p.amount for p in payments.filter(status='paid')),
            'amount_to_issue': self.total_amount - sum(p.amount for p in payments.exclude(status='cancelled'))
        }

    def update_payment_status(self):
        summary = self.payments_summary
        if summary['paid_amount'] >= self.total_amount:
            self.payment_status = 'paid'
        elif summary['paid_amount'] > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'not_paid'
        self.save()

    def __str__(self):
        return f'Invoice {self.ref} from {self.supplier.name}'

class InvoiceProduct(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reduction_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=[
        (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
    ], default=20.00)

    @property
    def subtotal(self):
        discount = (self.unit_price * self.quantity) * (self.reduction_rate / 100)
        return (self.unit_price * self.quantity) - discount

    @property
    def total_amount(self):
        return self.subtotal + (self.subtotal * (self.vat_rate / 100))

    def save(self, *args, **kwargs):
        if self.vat_rate == 0.00:
            self.vat_rate = self.product.vat_rate
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.product.name} on Invoice {self.invoice.ref}'
    
class ExportRecord(BaseModel):
    exported_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Export {self.filename} at {self.exported_at}"

class BankAccount(BaseModel):
    BANK_CHOICES = [
        ('ATW', 'Attijariwafa Bank'),
        ('BCP', 'Banque Populaire'),
        ('BOA', 'Bank of Africa'),
        ('CAM', 'Crédit Agricole du Maroc'),
        ('CIH', 'CIH Bank'),
        ('BMCI', 'BMCI'),
        ('SGM', 'Société Générale Maroc'),
        ('CDM', 'Crédit du Maroc'),
        ('ABB', 'Al Barid Bank'),
        ('CFG', 'CFG Bank'),
        ('ABM', 'Arab Bank Maroc'),
        ('CTB', 'Citibank Maghreb')
    ]

    ACCOUNT_TYPE = [
        ('national', 'National'),
        ('international', 'International')
    ]

    bank = models.CharField(max_length=4, choices=BANK_CHOICES)
    account_number = models.CharField(
        max_length=30,
        validators=[
            MinLengthValidator(10, 'Account number must be at least 10 characters'),
            RegexValidator(r'^\d+$', 'Only numeric characters allowed')
        ]
    )
    accounting_number = models.CharField(
        max_length=10,
        validators=[
            MinLengthValidator(5, 'Accounting number must be at least 5 characters'),
            RegexValidator(r'^\d+$', 'Only numeric characters allowed')
        ]
    )
    journal_number = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(r'^\d{2}$', 'Must be exactly 2 digits')
        ]
    )
    city = models.CharField(max_length=100)
    account_type = models.CharField(max_length=15, choices=ACCOUNT_TYPE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['bank', 'account_number']

    def __str__(self):
        type_indicator = 'NAT' if self.account_type == 'national' else 'INT'
        return f"{self.bank} [{self.account_number}] - {type_indicator}"
    
class Checker(BaseModel):
    TYPE_CHOICES = [
        ('CHQ', 'Cheque'),
        ('LCN', 'LCN')
    ]
    
    PAGE_CHOICES = [
        (25, '25'),
        (50, '50'),
        (100, '100')
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_use', 'In Use'), 
        ('completed', 'Completed')
    ]

    code = models.CharField(max_length=10, unique=True, blank=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)  # New field
    num_pages = models.IntegerField(choices=PAGE_CHOICES)
    index = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')]
    )
    starting_page = models.IntegerField(validators=[MinValueValidator(1)])
    final_page = models.IntegerField(blank=True)
    current_position = models.IntegerField(blank=True)
    is_active = models.BooleanField(default=True)
    owner = models.CharField(max_length=100, default="Briqueterie Sidi Kacem")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')

    def update_status(self):
        if self.current_position > self.starting_page:
            self.status = 'in_use'
        if self.current_position >= self.final_page:
            self.status = 'completed'
        self.save()

    def get_status(self):
        STATUS_STYLES = {
            'new': {'label': 'New', 'color': 'primary'},
            'in_use': {'label': 'In Use', 'color': 'warning'},
            'completed': {'label': 'Completed', 'color': 'success'},
        }
        return STATUS_STYLES.get(self.status, {'label': 'Unknown', 'color': 'secondary'})

    @property
    def remaining_pages(self):
        print(f"Calculating remaining pages for {self.bank_account.bank}")
        
        # Get all used positions (excluding cancelled checks)
        used_positions = set(
            self.checks.values_list('position', flat=True)
        )
        used_positions_count = self.checks.count()
        # Count available positions
        available_count = self.final_page - self.starting_page + 1 - used_positions_count
        print(f"Used positions: {used_positions}")
        print(f"Available positions count: {available_count}")
        
        return available_count
    def clean(self):
        if self.bank_account:
            if not self.bank_account.is_active:
                raise ValidationError("Cannot create checker for inactive bank account")
            if self.bank_account.account_type != 'national':
                raise ValidationError("Can only create checkers for national accounts")
        super().clean()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.final_page:
            self.final_page = self.starting_page + self.num_pages - 1
        if not self.current_position:
            self.current_position = self.starting_page
        super().save(*args, **kwargs)

    def generate_code(self):
        # Generate random alphanumeric code
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    #signature part#
    position_signatures = models.JSONField(default=dict)

    def get_position_signature_status(self, position):
        print(f"Getting signature status for position {position}")
        print(f"Current signatures: {self.position_signatures}")
        return self.position_signatures.get(str(position), {
            'signatures': [],
            'timestamps': []
        })

    def add_signature(self, position, signature):
        print(f"Adding signature {signature} to position {position}")
        position = str(position)
        if position not in self.position_signatures:
            print(f"Position {position} not found, initializing")
            self.position_signatures[position] = {
                'signatures': [],
                'timestamps': []
            }
        
        if signature not in self.position_signatures[position]['signatures']:
            print(f"Adding new signature {signature}")
            self.position_signatures[position]['signatures'].append(signature)
            self.position_signatures[position]['timestamps'].append(
                timezone.now().isoformat()
            )
            print(f"Updated signatures: {self.position_signatures}")
            self.save()
        else:
            print(f"Signature {signature} already exists for position {position}")
        
    
    def get_last_issued_check(self):
        """Get the last issued check."""
        return self.checks.exclude(status="available").order_by('-position').first()

    def get_next_available_position(self):
        """Calculate the next available position."""
        last_check = self.get_last_issued_check()
        if last_check:
            last_position = int(last_check.position[len(self.index):])
            next_position = last_position + 1
            if next_position <= self.final_page:
                return next_position
        return self.starting_page

    def __str__(self):
        return f'Checker {self.index}'

    class Meta:
        ordering = ['-created_at']

class Check(BaseModel):
    checker = models.ForeignKey(Checker, on_delete=models.PROTECT, related_name='checks')
    position = models.CharField(max_length=10, unique=True)  # Will store "INDEX + position number"
    creation_date = models.DateField(default=timezone.now)
    beneficiary = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    cause = models.ForeignKey(Invoice, on_delete=models.PROTECT)
    payment_due = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    observation = models.TextField(blank=True)
    delivered = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('printed', 'Printed'),
            ('ready_to_sign', 'Ready to Sign'),
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
            ('paid', 'Paid'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )

    REJECTION_REASONS = [
        ('insufficient_funds', 'Insufficient Funds'),
        ('signature_mismatch', 'Signature Mismatch'),
        ('amount_error', 'Amount Error'),
        ('date_error', 'Date Error'),
        ('other', 'Other')
    ]

    SIGNATURE_CHOICES = [
        ('OUK', 'OUK'),
        ('KEZ', 'KEZ')
    ]
    

    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS, null=True, blank=True)
    rejection_note = models.TextField(blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)

    replaces = models.ForeignKey('self', null=True, blank=True, related_name='replaced_by', on_delete=models.PROTECT)

    received_at = models.DateTimeField(null=True, blank=True)
    received_notes = models.TextField(blank=True)

    signatures = models.JSONField(default=list)

    
    def save(self, *args, **kwargs):
        print(f"New creation at:  {self.checker.current_position}")
        if not self.position:
            self.position = self.checker.current_position
        if not self.amount_due:
            self.amount_due = self.cause.total_amount
        super().save(*args, **kwargs)
        
        # Update checker's current position
        if self.checker.current_position == self.checker.current_position:
            self.checker.current_position += 1
            self.checker.save()

    def clean(self):
                
        # Ensure no duplicate positions
        if self.objects.filter(checker=self.checker, position=self.position).exists():
            raise ValidationError("This position is already used.")
        
        # Ensure the position is within the valid range
        if int(self.position[len(self.checker.index):]) < self.checker.starting_page or \
           int(self.position[len(self.checker.index):]) > self.checker.final_page:
            raise ValidationError(
                f"Position must be between {self.checker.starting_page} and {self.checker.final_page}."
            )
        
        if self.paid_at and not self.delivered_at:
            raise ValidationError("Check cannot be marked as paid before delivery")
        
        super().clean()

    class Meta:
        ordering = ['-creation_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__lte=models.F('amount_due')),
                name='check_amount_cannot_exceed_due'
            )
        ]
    
    @property
    def has_replacement(self):
        return hasattr(self, 'replaced_by') and self.replaced_by.exists()

    def reject(self, reason, note=''):
        self.status = 'rejected'
        self.rejection_reason = reason
        self.rejection_note = note
        self.rejection_date = timezone.now()
        self.save()

    def replace_with(self, new_check):
        new_check.replaces = self
        new_check.save()

    @property
    def is_received(self):
        """Check if we have physical possession of the check"""
        return bool(self.received_at)

    @property
    def can_be_replaced(self):
        """Can only replace rejected checks that we physically have"""
        return (
            self.status == 'rejected' and 
            self.is_received and 
            not self.has_replacement
        )

    def receive(self, notes=''):
        """Mark check as physically received"""
        if self.status not in ['delivered', 'rejected']:
            raise ValidationError("Only delivered or rejected checks can be received")
        
        self.received_at = timezone.now()
        self.received_notes = notes
        self.save()

    def create_replacement(self, checker, **kwargs):
        """
        Create a replacement check after validating state
        
        Args:
            checker (Checker): The checker to use for the new check
            **kwargs: Additional fields to override (amount, due date, etc.)
        """
        if not self.can_be_replaced:
            raise ValidationError(
                "Cannot replace: Check must be rejected and received, with no existing replacement"
            )

        if not checker.is_active or checker.status == 'completed':
            raise ValidationError("Selected checker is not available for new checks")

        # Create new check with same base properties but new checker and details
        replacement = Check.objects.create(
            checker=checker,  # Use the provided checker
            beneficiary=self.beneficiary,
            cause=self.cause,
            amount_due=self.amount_due,
            replaces=self,
            **kwargs  # Allow overriding specific fields like amount, due date
        )
        return replacement

    @property
    def signature_status(self):
        sig_count = len(self.signatures)
        if sig_count == 0:
            return 'unsigned'
        elif sig_count == 1:
            return 'mono-signed'
        return 'double-signed'

    def can_be_signed(self, signature):
        return (
            signature in dict(self.SIGNATURE_CHOICES) and
            signature not in self.signatures and
            len(self.signatures) < 2
        )

    def add_signature(self, signature):
        if self.can_be_signed(signature):
            self.signatures.append(signature)
            if len(self.signatures) == 2:
                self.status = 'pending'
            elif self.status == 'printed':
                self.status = 'ready_to_sign'
            self.save()

class Client(BaseModel):
    """
    Client model with manually entered client code.
    Inherits UUID from BaseModel but maintains a separate client_code field.
    """
    name = models.CharField(
        max_length=255, 
        null=False, 
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Name can only contain letters and spaces'
            )
        ]
    )
    
    client_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            MinLengthValidator(5, 'Client code must be at least 5 digits'),
            MaxLengthValidator(10, 'Client code cannot exceed 10 digits'),
            RegexValidator(
                regex=r'^\d+$',
                message='Client code must contain only digits'
            )
        ],
        help_text='Enter a unique 5-10 digit code'
    )

    def clean(self):
        """Additional model validation"""
        logger.debug(f"Validating Client: name={self.name}, code={self.client_code}")
        
        if self.client_code:
            try:
                code_length = len(self.client_code)
                if code_length < 5 or code_length > 10:
                    raise ValidationError({
                        'client_code': 'Client code must be between 5 and 10 digits'
                    })
            except Exception as e:
                logger.error(f"Validation error for client_code: {e}")
                raise
    
    # Add to Client model

    def get_transactions(self, year=None, month=None):
        """
        Get all transactions for the client with optional year/month filter.
        For sales: Uses the actual date
        For receipts: Uses the client_year and client_month fields
        """
        transactions = []
        
        # Get sales for the specified period (using actual date)
        sales_query = self.clientsale_set.all()
        if year:
            sales_query = sales_query.filter(date__year=year)
            if month:
                sales_query = sales_query.filter(date__month=month)
                
        for sale in sales_query:
            transactions.append({
                'date': sale.date,
                'type': 'SALE',
                'description': f'Sales of {sale.date.strftime("%m-%Y")}',
                'debit': sale.amount,
                'credit': None,
                'actual_date': sale.date  # Store actual date for sorting
            })

        # Calculate previous balance using client_year and client_month for receipts
        if year and month:
            current_date = datetime.date(int(year), int(month), 1)
            previous_balance = 0
            
            # Previous Sales (by actual date)
            prev_sales = self.clientsale_set.filter(date__lt=current_date)
            for sale in prev_sales:
                previous_balance += sale.amount

            # Previous Checks (by client year/month)
            prev_checks = CheckReceipt.objects.filter(
                client=self
            ).filter(
                Q(client_year__lt=year) | 
                Q(client_year=year, client_month__lt=month)
            )
            for check in prev_checks:
                previous_balance -= check.amount

            # Previous LCNs (by client year/month)
            prev_lcns = LCN.objects.filter(
                client=self
            ).filter(
                Q(client_year__lt=year) | 
                Q(client_year=year, client_month__lt=month)
            )
            for lcn in prev_lcns:
                previous_balance -= lcn.amount

            # Previous Transfers (by client year/month)
            prev_transfers = TransferReceipt.objects.filter(
                client=self
            ).filter(
                Q(client_year__lt=year) | 
                Q(client_year=year, client_month__lt=month)
            )
            for transfer in prev_transfers:
                previous_balance -= transfer.amount

            # Previous Cash (by client year/month)
            prev_cash = CashReceipt.objects.filter(
                client=self
            ).filter(
                Q(client_year__lt=year) | 
                Q(client_year=year, client_month__lt=month)
            )
            for cash in prev_cash:
                previous_balance -= cash.amount

            if previous_balance != 0:
                transactions.append({
                    'date': current_date,
                    'type': 'BALANCE',
                    'description': 'Previous Balance',
                    'debit': previous_balance if previous_balance > 0 else None,
                    'credit': abs(previous_balance) if previous_balance < 0 else None,
                    'balance': previous_balance,
                    'actual_date': current_date
                })

        # Get receipts for the specified period (using client_year/month)
        if year and month:
            # Checks for this period
            checks_query = CheckReceipt.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            )
            for check in checks_query:
                transactions.append({
                    'date': check.operation_date,
                    'type': 'CHECK',
                    'description': (f'CHQ {check.check_number} {check.entity.name} '
                                f'(received on {check.operation_date.strftime("%Y-%m-%d")})'),
                    'debit': None,
                    'credit': check.amount,
                    'actual_date': check.operation_date
                })

            # LCNs for this period
            lcns_query = LCN.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            )
            for lcn in lcns_query:
                transactions.append({
                    'date': lcn.operation_date,
                    'type': 'LCN',
                    'description': (f'LCN {lcn.lcn_number} {lcn.entity.name} '
                                f'(received on {lcn.operation_date.strftime("%Y-%m-%d")}, '
                                f'due on {lcn.due_date.strftime("%Y-%m-%d")})'),
                    'debit': None,
                    'credit': lcn.amount,
                    'actual_date': lcn.operation_date
                })

            # Similar updates for Transfer and Cash receipts...
            transfers_query = TransferReceipt.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            )
            for transfer in transfers_query:
                transactions.append({
                    'date': transfer.operation_date,
                    'type': 'TRANSFER',
                    'description': (f'Transfer from {transfer.entity.name} '
                                f'(received on {transfer.operation_date.strftime("%Y-%m-%d")})'),
                    'debit': None,
                    'credit': transfer.amount,
                    'actual_date': transfer.operation_date
                })

            cash_query = CashReceipt.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            )
            for cash in cash_query:
                transactions.append({
                    'date': cash.operation_date,
                    'type': 'CASH',
                    'description': f'Cash (received on {cash.operation_date.strftime("%Y-%m-%d")})',
                    'debit': None,
                    'credit': cash.amount,
                    'actual_date': cash.operation_date
                })

        # Sort transactions:
        # 1. Balance entries first
        # 2. Then by actual date
        transactions.sort(key=lambda x: (
            x['type'] != 'BALANCE',  # Balance entries first
            x['actual_date']  # Then by actual date
        ))

        # Calculate running balance
        balance = previous_balance if year and month else 0
        for t in transactions:
            if t['type'] != 'BALANCE':  # Skip balance entries
                balance += (t['debit'] or 0) - (t['credit'] or 0)
            t['balance'] = balance

        return transactions

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs"""
        logger.info(f"Saving Client: {self.name}")
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Successfully saved Client: {self.name} with code {self.client_code}")

    def __str__(self):
        return f"{self.name} ({self.client_code})"

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Entity(BaseModel):
    """
    Entity model with strict validation for ICE and accounting codes.
    """
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Name can only contain letters and spaces'
            )
        ]
    )
    
    ice_code = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{15}$',
                message='ICE code must be exactly 15 digits'
            )
        ],
        help_text='Enter exactly 15 digits'
    )
    
    accounting_code = models.CharField(
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^3\d{4,6}$',
                message='Accounting code must start with 3 and be 5-7 digits long'
            )
        ],
        help_text='Enter 5-7 digits starting with 3'
    )
    
    # Optional fields
    city = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        """Additional model validation"""
        logger.debug(f"Validating Entity: name={self.name}, ice={self.ice_code}, accounting={self.accounting_code}")
        
        # Validate ICE code
        if self.ice_code and not self.ice_code.isdigit():
            raise ValidationError({
                'ice_code': 'ICE code must contain only digits'
            })
            
        # Validate accounting code
        if self.accounting_code:
            if not self.accounting_code.startswith('3'):
                raise ValidationError({
                    'accounting_code': 'Accounting code must start with 3'
                })
            if not self.accounting_code.isdigit():
                raise ValidationError({
                    'accounting_code': 'Accounting code must contain only digits'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs"""
        logger.info(f"Saving Entity: {self.name}")
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Successfully saved Entity: {self.name}")

    def __str__(self):
        return f"{self.name} ({self.ice_code})"

    class Meta:
        ordering = ['name']
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'



class Receipt(BaseModel):
    """Base class for all receipt types."""
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    entity = models.ForeignKey('Entity', on_delete=models.PROTECT)
    operation_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    client_year = models.IntegerField()
    client_month = models.IntegerField()
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.client_year:
            self.client_year = timezone.now().year
        if not self.client_month:
            self.client_month = timezone.now().month
        super().save(*args, **kwargs)

class NegotiableReceipt(Receipt):
    """Base class for checks and LCNs."""
    STATUS_PORTFOLIO = 'PORTFOLIO'
    STATUS_PRESENTED_COLLECTION = 'PRESENTED_COLLECTION'
    STATUS_PRESENTED_DISCOUNT = 'PRESENTED_DISCOUNT'
    STATUS_DISCOUNTED = 'DISCOUNTED'
    STATUS_PAID = 'PAID'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPENSATED = 'COMPENSATED'

    RECEIPT_STATUS = [
        (STATUS_PORTFOLIO, 'In Portfolio'),
        (STATUS_PRESENTED_COLLECTION, 'Presented for Collection'),
        (STATUS_PRESENTED_DISCOUNT, 'Presented for Discount'),
        (STATUS_DISCOUNTED, 'Discounted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPENSATED, 'Compensated')
    ]

    due_date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=RECEIPT_STATUS,
        default=STATUS_PORTFOLIO
    )
    compensates = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='compensated_by'
    )

    class Meta:
        abstract = True

    def can_be_presented(self):
        return self.status == self.STATUS_PORTFOLIO

    def present_for_collection(self):
        if not self.can_be_presented():
            raise ValidationError("Receipt cannot be presented")
        self.status = self.STATUS_PRESENTED_COLLECTION
        self.save()

    def present_for_discount(self):
        if not self.can_be_presented():
            raise ValidationError("Receipt cannot be presented")
        self.status = self.STATUS_PRESENTED_DISCOUNT
        self.save()

class CheckReceipt(NegotiableReceipt):
    """Check-specific implementation."""
    check_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Check {self.check_number} - {self.amount}"

    class Meta:
        verbose_name = "Check"
        verbose_name_plural = "Checks"

class LCN(NegotiableReceipt):
    """LCN-specific implementation."""
    lcn_number = models.CharField(max_length=50)
    issuing_bank = models.CharField(max_length=100)

    def __str__(self):
        return f"LCN {self.lcn_number} - {self.amount}"

    def clean(self):
        super().clean()
        if not self.due_date:
            raise ValidationError("Due date is required for LCN")

    class Meta:
        verbose_name = "LCN"
        verbose_name_plural = "LCNs"

class CashReceipt(Receipt):
    """Cash receipt implementation."""
    reference_number = models.CharField(max_length=50, blank=True)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='cash_receipts'
    )

    def __str__(self):
        return f"Cash Receipt {self.id} - {self.amount}"

    class Meta:
        verbose_name = "Cash Receipt"
        verbose_name_plural = "Cash Receipts"

class TransferReceipt(Receipt):
    """Bank transfer implementation."""
    transfer_reference = models.CharField(max_length=100)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='transfer_receipts'
    )
    transfer_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Transfer {self.transfer_reference} - {self.amount}"

    class Meta:
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"

class Presentation(BaseModel):
    """Represents a collection/discount presentation of negotiable receipts."""
    TYPE_COLLECTION = 'COLLECTION'
    TYPE_DISCOUNT = 'DISCOUNT'
    
    PRESENTATION_TYPES = [
        (TYPE_COLLECTION, 'Collection'),
        (TYPE_DISCOUNT, 'Discount')
    ]

    presentation_type = models.CharField(max_length=10, choices=PRESENTATION_TYPES)
    date = models.DateField()
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_presentation_type_display()} - {self.date}"

    @property
    def receipt_count(self):
        return self.presentation_receipts.count()

    def update_total(self):
        self.total_amount = sum(
            pr.amount for pr in self.presentation_receipts.all()
        )
        self.save()

    def clean(self):
        super().clean()
        self.validate_receipts()

    def validate_receipts(self):
        invalid_receipts = self.presentation_receipts.exclude(
            receipt__status=NegotiableReceipt.STATUS_PORTFOLIO
        )
        if invalid_receipts.exists():
            raise ValidationError('All receipts must be in portfolio status')

    class Meta:
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
        ordering = ['-date', '-created_at']

class PresentationReceipt(BaseModel):
    """Links receipts to presentations."""
    presentation = models.ForeignKey(
        Presentation, 
        on_delete=models.CASCADE,
        related_name='presentation_receipts'
    )
    checkreceipt = models.ForeignKey(
        CheckReceipt, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='check_presentations'
    )
    lcn = models.ForeignKey(
        LCN, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lcn_presentations'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        receipt = self.check or self.lcn
        return f"Presentation {self.presentation.id} - Receipt {receipt.id}"

    def clean(self):
        super().clean()
        if self.check and self.lcn:
            raise ValidationError("Cannot have both check and LCN")
        if not self.check and not self.lcn:
            raise ValidationError("Must have either check or LCN")
        
        receipt = self.check or self.lcn
        if receipt.status != NegotiableReceipt.STATUS_PORTFOLIO:
            raise ValidationError(
                'Only receipts in portfolio status can be presented'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.presentation.update_total()

        # Update receipt status
        receipt = self.check or self.lcn
        if self.presentation.presentation_type == Presentation.TYPE_COLLECTION:
            receipt.present_for_collection()
        else:
            receipt.present_for_discount()

    class Meta:
        verbose_name = "Presentation Receipt"
        verbose_name_plural = "Presentation Receipts"
        unique_together = [
            ('presentation', 'checkreceipt'),
            ('presentation', 'lcn')
        ]

class ClientSale(BaseModel):
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    year = models.IntegerField()  # For easy filtering
    month = models.IntegerField()  # For easy filtering
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.year:
            self.year = self.date.year
        if not self.month:
            self.month = self.date.month
        super().save(*args, **kwargs)
```

# services.py

```py
from django.core.exceptions import ValidationError
from django.db import transaction

def create_check(
    checker,
    position,
    creation_date,
    beneficiary,
    cause,
    payment_due,
    amount,
    observation
):
    """
    Create a check with validation and transactional safety.

    Args:
        checker (Checker): The associated checker instance.
        position (int): The position for the check.
        creation_date (date): The creation date for the check.
        beneficiary (Supplier): The supplier to whom the check is issued.
        cause (Invoice): The invoice causing the check.
        payment_due (date): The payment due date for the check.
        amount (Decimal): The amount of the check.
        observation (str): Additional notes or observations.

    Returns:
        Check: The created Check instance.

    Raises:
        ValidationError: If validation fails.
    """
    # Validate duplicate position
    if checker.checks.filter(position=position).exists():
        raise ValidationError(f"Position {position} is already used.")

    # Validate range
    if position < checker.starting_page or position > checker.final_page:
        raise ValidationError(
            f"Position must be between {checker.starting_page} and {checker.final_page}."
        )

    # Transaction to ensure atomicity
    with transaction.atomic():
        check = Check.objects.create(
            checker=checker,
            position=position,
            creation_date=creation_date,
            beneficiary=beneficiary,
            cause=cause,
            payment_due=payment_due,
            amount=amount,
            observation=observation
        )

        # Update checker's current position
        next_position = checker.current_position + 1
        if next_position <= checker.final_page:
            checker.current_position = next_position
            checker.save()

    return check

```

# signals.py

```py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Check

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Create a Profile for new users
        Profile.objects.create(user=instance)
    else:
        # Save the Profile if it already exists
        if hasattr(instance, 'profile'):
            instance.profile.save()


@receiver(post_save, sender=Check)
def update_invoice_payment_status(sender, instance, **kwargs):
    if instance.cause:
        instance.cause.update_payment_status()


@receiver(post_save, sender=Check)
def update_checker_status(sender, instance, **kwargs):
    if instance.checker:
        instance.checker.update_status()


```

# templates/bank/bank_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Bank Accounts</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#bankModal"> <i class="fas fa-plus"></i> Add Bank Account </button> </div> <!-- Filter Section --> <div class="filter-section mb-4"> <div class="d-flex flex-wrap gap-3"> <div class="flex-grow-1"> <select class="form-control" id="bankFilter"> <option value="">All Banks</option> {% for code, name in bank_choices %} <option value="{{ code }}">{{ name }}</option> {% endfor %} </select> </div> <div class="flex-grow-1"> <select class="form-control" id="accountTypeFilter"> <option value="">All Types</option> <option value="national">National</option> <option value="international">International</option> </select> </div> <div class="flex-grow-1"> <input type="text" class="form-control" id="searchAccount" placeholder="Search account number..."> </div> </div> </div> <!-- Accounts Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Bank</th> <th>Account Number</th> <th>Journal</th> <th>City</th> <th>Type</th> <th>Status</th> <th>Creation</th> <th>Actions</th> </tr> </thead> <tbody id="accountsTableBody"> {% include 'bank/partials/accounts_table.html' %} </tbody> </table> </div> </div> <!-- Bank Account Modal --> <div class="modal fade" id="bankModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Add Bank Account</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <form id="bank-account-form"> {% csrf_token %} <div class="modal-body"> <div class="row"> <div class="col-12"> <div class="form-group"> <label>Bank</label> <select class="form-control" id="bank" name="bank"> {% for code, name in bank_choices %} <option value="{{ code }}">{{ name }}</option> {% endfor %} </select> <div class="invalid-feedback">Please select a bank</div> </div> </div> <div class="col-12"> <div class="form-group"> <label>Account Number</label> <input type="text" class="form-control" id="accountNumber" placeholder="Enter account number"> <div class="invalid-feedback"> Must be at least 10 numeric characters </div> <small class="text-muted">Minimum 10 digits, numbers only</small> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Accounting Number</label> <input type="text" class="form-control" id="accountingNumber" placeholder="Min. 5 digits"> <div class="invalid-feedback"> Must be at least 5 numeric characters </div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Journal Number</label> <input type="text" class="form-control" id="journalNumber" placeholder="2 digits" maxlength="2"> <div class="invalid-feedback"> Must be exactly 2 digits </div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>City</label> <input type="text" class="form-control" id="city" placeholder="Enter city"> <div class="invalid-feedback">City is required</div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Account Type</label> <select class="form-control" id="accountType"> <option value="national">National</option> <option value="international">International</option> </select> </div> </div> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveBankAccount" disabled> Create Account </button> </div> </form> </div> </div> </div> <style> /* Real-time validation styles */ .form-control.is-typing { border-color: #80bdff; box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25); } .form-control.is-valid { border-color: #28a745; padding-right: calc(1.5em + 0.75rem); background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e"); background-repeat: no-repeat; background-position: right calc(0.375em + 0.1875rem) center; background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem); } .form-control.is-invalid { border-color: #dc3545; padding-right: calc(1.5em + 0.75rem); background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='%23dc3545' viewBox='0 0 12 12'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e"); background-repeat: no-repeat; background-position: right calc(0.375em + 0.1875rem) center; background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem); } </style> <script> console.log('Script starting...'); // Debug function function debug(context, message, data = null) { const debugMsg = `[${context}] ${message}`; if (data) { console.log(debugMsg, data); } else { console.log(debugMsg); } } const BankAccountModal = { init() { this.modal = $('#bankModal'); this.form = this.modal.find('form'); this.saveBtn = $('#saveBankAccount'); this.setupValidation(); this.bindEvents(); }, setupValidation() { // Account number validation $('#accountNumber').on('input', function() { const value = this.value.replace(/\D/g, ''); // Removed non-digits this.value = value; $(this).toggleClass('is-valid', value.length >= 10) .toggleClass('is-invalid', value.length > 0 && value.length < 10); BankAccountModal.checkFormValidity(); }); // Accounting number validation $('#accountingNumber').on('input', function() { const value = this.value.replace(/\D/g, ''); // Removed non-digits this.value = value; $(this).toggleClass('is-valid', value.length >= 5) .toggleClass('is-invalid', value.length > 0 && value.length < 5); BankAccountModal.checkFormValidity(); }); // Journal number validation $('#journalNumber').on('input', function() { const value = this.value.replace(/\D/g, ''); // Removed non-digits this.value = value.slice(0, 2); // Restrict to two characters $(this).toggleClass('is-valid', value.length === 2) .toggleClass('is-invalid', value.length > 0 && value.length !== 2); BankAccountModal.checkFormValidity(); }); // City validation $('#city').on('input', function() { $(this).toggleClass('is-valid', this.value.length > 0) .toggleClass('is-invalid', this.value.length === 0); BankAccountModal.checkFormValidity(); }); }, bindEvents() { // Form submission console.log("Binding events..."); this.form.on('submit', (e) => { e.preventDefault(); this.saveAccount(); }); this.saveBtn.on('click', () => { console.log("Save button clicked!"); this.form.trigger('submit'); // Trigger the form submission manually }); // Modal reset on close this.modal.on('hidden.bs.modal', () => { this.resetForm(); }); }, checkFormValidity() { const isValid = $('#accountNumber').val().length >= 10 && $('#accountingNumber').val().length >= 5 && $('#journalNumber').val().length === 2 && $('#city').val().length > 0; this.saveBtn.prop('disabled', !isValid); }, async saveAccount() { const data = { bank: $('#bank').val(), account_number: $('#accountNumber').val(), accounting_number: $('#accountingNumber').val(), journal_number: $('#journalNumber').val(), city: $('#city').val(), account_type: $('#accountType').val() }; try { const csrfToken = this.form.find('[name=csrfmiddlewaretoken]').val(); if (!csrfToken) { throw new Error('CSRF token not found'); } const response = await fetch('/testapp/bank-accounts/create/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken }, body: JSON.stringify(data) }); if (!response.ok) { const error = await response.json(); // Parse JSON for error message throw new Error(error.error || 'Failed to create bank account'); } // Success handling this.modal.modal('hide'); location.reload(); // Reload to reflect changes } catch (error) { console.error('Save error:', error); alert(error.message); // Display error in alert } }, resetForm() { $('#bankModal input').val('').removeClass('is-valid is-invalid'); // Reset form inputs $('#bank, #accountType').prop('selectedIndex', 0); // Reset select fields this.saveBtn.prop('disabled', true); // Disable the save button } }; // Filter functionality const BankAccountFilters = { init() { console.log("Initializing BankAccountFilters"); this.bindFilters(); this.setupSearch(); }, bindFilters() { console.log("Binding filter events"); $('#bankFilter, #accountTypeFilter').on('change', () => { console.log("Filter changed"); this.applyFilters(); }); }, setupSearch() { console.log("Setting up search functionality"); let timeout; $('#searchAccount').on('input', () => { clearTimeout(timeout); timeout = setTimeout(() => this.applyFilters(), 300); // Add debounce for performance }); }, async applyFilters() { console.log("Applying filters"); const filters = { bank: $('#bankFilter').val(), type: $('#accountTypeFilter').val(), search: $('#searchAccount').val() }; console.log("Filter values:", filters); try { const response = await fetch(`/testapp/bank-accounts/filter/?${new URLSearchParams(filters)}`); if (!response.ok) throw new Error('Filter request failed'); const data = await response.json(); $('#accountsTableBody').html(data.html); // Update table body console.log("Filters applied successfully"); } catch (error) { console.error('Error applying filters:', error); } } }; // Handle account deactivation $('.deactivate-account').on('click', async function() { if (!confirm('Are you sure you want to deactivate this account?')) return; const accountId = $(this).data('account-id'); try { const response = await fetch(`/testapp/bank-accounts/${accountId}/deactivate/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }); if (!response.ok) { throw new Error(await response.text()); } location.reload(); } catch (error) { alert('Error deactivating account: ' + error.message); // Handle error gracefully } }); $(document).ready(() => { console.log('Initializing Bank Account Modal...'); BankAccountModal.init(); BankAccountFilters.init(); }); </script> {% endblock %}
```

# templates/bank/partials/accounts_table.html

```html
{% for account in accounts %} <tr> <td> <div class="d-flex align-items-center"> <span class="bank-logo {{ account.bank|lower }}"></span> <span class="ml-2">{{ account.get_bank_display }}</span> </div> </td> <td>{{ account.account_number }}</td> <td>{{ account.journal_number }}</td> <td>{{ account.city }}</td> <td> <span class="badge {% if account.account_type == 'national' %}badge-primary{% else %}badge-info{% endif %}"> {{ account.get_account_type_display }} </span> </td> <td> <span class="badge {% if account.is_active %}badge-success{% else %}badge-danger{% endif %}"> {{ account.is_active|yesno:"Active,Inactive" }} </span> </td> <td>{{ account.created_at|date:"d/m/Y" }}</td> <td> {% if account.is_active %} <button class="btn btn-sm btn-danger deactivate-account" data-account-id="{{ account.id }}" {% if account.has_active_checkers %}disabled{% endif %} title="{% if account.has_active_checkers %}Cannot deactivate: Has active checkers{% endif %}"> <i class="fas fa-times"></i> </button> {% endif %} </td> </tr> {% endfor %}
```

# templates/base.html

```html
<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>{% block title %}BSK Management{% endblock %}</title> <!-- CSS --> <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet"> <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet"> <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet"> <link href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css" rel="stylesheet"> <!-- Custom Styles --> <style> :root { --primary-color: #2563eb; --sidebar-width: 250px; --topbar-height: 60px; --transition-speed: 0.3s; } body { min-height: 100vh; background-color: #f8fafc; padding-top: var(--topbar-height) } /* Sidebar Styling */ #sidebar { width: var(--sidebar-width); height: 100vh; position: fixed; left: 0; top: 0; background: #1e293b; transition: transform var(--transition-speed); z-index: 1000; } #sidebar.collapsed { transform: translateX(-100%); } #sidebar .nav-link { color: #e2e8f0; padding: 0.8rem 1rem; transition: all var(--transition-speed); } #sidebar .nav-link:hover { background: rgba(255, 255, 255, 0.1); transform: translateX(5px); } #sidebar .nav-link.active { background: var(--primary-color); color: white; } /* Dropdown menu styling */ .nav-dropdown { background: rgba(255, 255, 255, 0.05); } .nav-dropdown .nav-link { padding-left: 2.5rem !important; font-size: 0.9rem; opacity: 0.9; } .nav-item-parent > .nav-link { display: flex; justify-content: space-between; align-items: center; } .nav-item-parent > .nav-link::after { content: '\f107'; font-family: 'Font Awesome 5 Free'; font-weight: 900; transition: transform 0.3s; } .nav-item-parent > .nav-link[aria-expanded="true"]::after { transform: rotate(180deg); } .collapse { transition: all 0.3s ease; } /* Main Content */ #main-content { margin-left: var(--sidebar-width); padding-top: var(--topbar-height); transition: margin var(--transition-speed); padding: 20px; margin-top: 0; } #main-content.expanded { margin-left: 0; } /* Topbar */ #topbar { height: var(--topbar-height); background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); position: fixed; top: 0; right: 0; left: var(--sidebar-width); z-index: 999; transition: left var(--transition-speed); } #topbar.expanded { left: 0; } /* Modal Animations */ .modal.fade .modal-dialog { transform: scale(0.8); transition: transform var(--transition-speed); } .modal.show .modal-dialog { transform: scale(1); } .modal { z-index: 1050; } /* Toast Animations */ .toast { position: fixed; top: 20px; right: 20px; z-index: 1050; animation: slideIn 0.3s ease-out; } @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } } /* Card Hover Effects */ .card { transition: transform 0.2s, box-shadow 0.2s; } .card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); } /* Button Hover Effects */ .btn { transition: all 0.2s; } .btn:hover { transform: translateY(-1px); } /* Table Row Hover */ .table-hover tbody tr { transition: background-color 0.2s; } /* Select2 Styling */ .select2-container--default .select2-selection--single { height: 38px; border: 1px solid #ced4da; border-radius: 0.375rem; } .select2-container--default .select2-selection--single .select2-selection__rendered { line-height: 38px; } /* Ensure dropdowns appear above other elements */ .dropdown-menu { z-index: 1000; } /* Keep autocomplete dropdown above other elements */ .ui-autocomplete { z-index: 2000; } </style> <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script> <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script> </head> <body> <!-- Sidebar --> <nav id="sidebar"> <div class="d-flex flex-column h-100"> <div class="p-3 text-center"> <h5 class="text-white mb-0">BSK Management</h5> </div> <ul class="nav flex-column mt-2"> <li class="nav-item"> <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" href="{% url 'home' %}"> <i class="fas fa-home me-2"></i> Dashboard </a> </li> <!-- Business Operations Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'business' in request.path %}active{% endif %}" data-toggle="collapse" href="#businessSubmenu" role="button" aria-expanded="false" aria-controls="businessSubmenu"> <span><i class="fas fa-briefcase me-2"></i> Business Operations</span> </a> <div class="collapse nav-dropdown" id="businessSubmenu"> <a class="nav-link {% if 'supplier' in request.path %}active{% endif %}" href="{% url 'supplier-list' %}"> <i class="fas fa-truck me-2"></i> Suppliers </a> <a class="nav-link {% if 'product' in request.path %}active{% endif %}" href="{% url 'product-list' %}"> <i class="fas fa-box-open me-2"></i> Products </a> <a class="nav-link {% if 'invoice' in request.path %}active{% endif %}" href="{% url 'invoice-list' %}"> <i class="fas fa-file-invoice-dollar me-2"></i> Invoices </a> </div> </li> <!-- Clients Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'client' in request.path %}active{% endif %}" data-toggle="collapse" href="#clientSubmenu" role="button" aria-expanded="false" aria-controls="clientSubmenu"> <span><i class="fas fa-users me-2"></i> Clients</span> </a> <div class="collapse nav-dropdown" id="clientSubmenu"> <a class="nav-link {% if 'receipt' in request.path %}active{% endif %}" href="{% url 'receipt-list' %}"> <i class="fas fa-receipt me-2"></i> Receipts </a> <a class="nav-link {% if 'client_management' in request.path %}active{% endif %}" href="{% url 'client_management' %}"> <i class="fas fa-address-card me-2"></i> Clients </a> <a class="nav-link {% if 'sale-list' in request.path %}active{% endif %}" href="{% url 'sale-list' %}"> <i class="fas fa-shopping-cart me-2"></i> Sales </a> </div> </li> <!-- Financial Management Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'financial' in request.path %}active{% endif %}" data-toggle="collapse" href="#financialSubmenu" role="button" aria-expanded="false" aria-controls="financialSubmenu"> <span><i class="fas fa-money-bill-wave me-2"></i> Financial Management</span> </a> <div class="collapse nav-dropdown" id="financialSubmenu"> <a class="nav-link {% if 'bank-account' in request.path %}active{% endif %}" href="{% url 'bank-account-list' %}"> <i class="fas fa-university me-2"></i> Bank Accounts </a> <a class="nav-link {% if 'checks' in request.path %}active{% endif %}" href="{% url 'check-list' %}"> <i class="fas fa-money-check me-2"></i> Checks </a> <a class="nav-link {% if 'checkers' in request.path %}active{% endif %}" href="{% url 'checker-list' %}"> <i class="fas fa-user-shield me-2"></i> Checkers </a> </div> </li> <!-- Bottom Section --> <div class="mt-auto p-3"> <div class="dropdown"> <button class="btn btn-dark dropdown-toggle w-100" type="button" data-bs-toggle="dropdown"> <i class="fas fa-user-circle me-2"></i> {{ request.user.username }} </button> <ul class="dropdown-menu dropdown-menu-dark w-100"> <li> <a class="dropdown-item" href="{% url 'profile' %}"> <i class="fas fa-id-card me-2"></i> Profile </a> </li> <li><hr class="dropdown-divider"></li> <li> <a class="dropdown-item text-danger" href="{% url 'logout' %}"> <i class="fas fa-sign-out-alt me-2"></i> Logout </a> </li> </ul> </div> </div> </div> </nav> <!-- Topbar --> <nav id="topbar" class="px-4 d-flex align-items-center"> <button id="sidebar-toggle" class="btn btn-link"> <i class="fas fa-bars"></i> </button> <div class="ms-auto d-flex align-items-center"> <div class="dropdown"> <button class="btn btn-link dropdown-toggle" type="button" data-bs-toggle="dropdown"> <i class="fas fa-bell"></i> <span class="badge bg-danger">3</span> </button> <ul class="dropdown-menu dropdown-menu-end"> <li><h6 class="dropdown-header">Notifications</h6></li> <li><a class="dropdown-item" href="#">New invoice added</a></li> <li><a class="dropdown-item" href="#">Payment received</a></li> <li><a class="dropdown-item" href="#">Check due today</a></li> </ul> </div> </div> </nav> <!-- Main Content --> <main id="main-content" class="p-4"> {% block content %}{% endblock %} </main> <!-- Scripts --> <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script> <script> $(document).ready(function() { // Sidebar Toggle $('#sidebar-toggle').click(function() { $('#sidebar').toggleClass('collapsed'); $('#main-content').toggleClass('expanded'); $('#topbar').toggleClass('expanded'); }); // Initialize Select2 $('.select2').select2({ theme: 'bootstrap' }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); // Keep submenu open if a child is active if ($('#clientSubmenu .nav-link.active').length) { $('#clientSubmenu').addClass('show'); $('#clientSubmenu').prev('.nav-link').attr('aria-expanded', 'true'); } }); // Toast function function showToast(message, type = 'success') { const toast = ` <div class="toast align-items-center text-white bg-${type}" role="alert"> <div class="d-flex"> <div class="toast-body">${message}</div> <button type="button" class="close ml-2 mb-1" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> </div> `; const toastContainer = $('<div>', { class: 'position-fixed', style: 'top: 20px; right: 20px; z-index: 1060;' }).html(toast); $('body').append(toastContainer); toastContainer.find('.toast').toast({ delay: 3000 }).toast('show'); toastContainer.find('.toast').on('hidden.bs.toast', function() { toastContainer.remove(); }); } </script> {% block extra_js %}{% endblock %} </body> </html>
```

# templates/checker/check_list.html

```html
{% extends 'base.html' %} {% load check_tags %} {% block content %} {% csrf_token %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Checks</h2> <div class="btn-group"> <button class="btn btn-primary" id="toggle-filters"> <i class="fas fa-filter"></i> Filters <span class="badge badge-light ml-2 active-filters-count" style="display:none">0</span> </button> </div> </div> <!-- Filter Panel --> <div class="filter-panel card mb-4" style="display:none"> <div class="card-body"> <div class="row"> <div class="col-md-3"> <select class="form-control" id="bankFilter"> <option value="">All Banks</option> {% for bank in banks %} <option value="{{ bank.bank }}">{{ bank.get_bank_display }}</option> {% endfor %} </select> </div> <div class="col-md-3"> <select class="form-control" id="statusFilter"> <option value="">All Status</option> <option value="pending">Pending</option> <option value="delivered">Delivered</option> <option value="paid">Paid</option> <option value="rejected">Rejected</option> <option value="cancelled">Cancelled</option> </select> </div> <div class="col-md-3"> <select class="form-control select2" id="beneficiaryFilter"> <option value="">All Beneficiaries</option> </select> </div> <div class="col-md-3"> <input type="text" class="form-control" id="searchCheck" placeholder="Search..."> </div> </div> </div> </div> <!-- Checks Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Reference</th> <th>Bank</th> <th>Creation Date</th> <th>Beneficiary</th> <th>Invoice Ref</th> <th>Amount Due</th> <th>Amount</th> <th>Due Date</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody id="checksTableBody"> {% include 'checker/partials/checks_table.html' %} </tbody> </table> </div> </div> {% include 'checker/partials/check_action_modals.html' %} <script> function formatMoney(amount) { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'MAD', minimumFractionDigits: 2 }).format(amount); } const CheckFilters = { init() { console.log("Initializing check filters"); this.bindFilters(); this.setupSelect2(); this.setupActionHandlers(); }, bindFilters() { console.log("Binding filter events"); $('#bankFilter, #statusFilter').on('change', () => { console.log("Filter changed"); this.applyFilters(); }); let timeout; $('#searchCheck').on('input', () => { clearTimeout(timeout); timeout = setTimeout(() => this.applyFilters(), 300); }); }, setupSelect2() { $('#beneficiaryFilter').select2({ placeholder: 'Search beneficiary...', allowClear: true, ajax: { url: "{% url 'supplier-autocomplete' %}", dataType: 'json', delay: 250, processResults: function(data) { return { results: data.map(item => ({ id: item.value, text: item.label })) }; } } }).on('change', () => this.applyFilters()); }, async applyFilters() { console.log("Applying filters"); const filters = { bank: $('#bankFilter').val(), status: $('#statusFilter').val(), beneficiary: $('#beneficiaryFilter').val(), search: $('#searchCheck').val() }; try { const response = await fetch(`/testapp/checks/filter/?${new URLSearchParams(filters)}`); if (!response.ok) throw new Error('Filter request failed'); const data = await response.json(); $('#checksTableBody').html(data.html); // Update filter count badge const activeFilters = Object.values(filters).filter(Boolean).length; const badge = $('.active-filters-count'); activeFilters > 0 ? badge.show().text(activeFilters) : badge.hide(); } catch (error) { console.error('Error applying filters:', error); } }, setupActionHandlers() { // Handle check actions (deliver, pay, etc.) $(document).on('click', '.check-action', (e) => { const button = $(e.currentTarget); this.handleCheckAction( button.data('action'), button.data('check-id') ); }); // Handle status badge clicks $(document).on('click', '.status-badge', (e) => { const checkId = $(e.currentTarget).data('check-id'); this.showCheckDetails(checkId); }); // Use delegate events for modal buttons $(document).on('click', '#confirm-cancel', (e) => { e.preventDefault(); console.log("Cancel confirm clicked"); this.handleCancel(); }); $(document).on('click', '#confirm-reject', (e) => { e.preventDefault(); console.log("Reject confirm clicked"); this.handleReject(); }); $(document).on('click', '#confirm-receive', (e) => { e.preventDefault(); this.handleReceiveAction(); }); $(document).on('click', '#create-replacement', (e) => { e.preventDefault(); this.handleCreateReplacement(); }); $(document).on('click', '#confirm-receive', (e) => { e.preventDefault(); this.handleReceiveAction(); }); }, async handleCheckAction(action, checkId) { switch (action) { case 'cancel': console.log("Opening cancel modal for check:", checkId); $('#cancelModal').modal('show'); $('#confirm-cancel').data('check-id', checkId); break; case 'reject': console.log("Opening reject modal for check:", checkId); $('#rejectModal').modal('show'); $('#confirm-reject').data('check-id', checkId); break; case 'receive': console.log("Opening receive modal for check:", checkId); $('#receiveModal').modal('show'); $('#confirm-receive').data('check-id', checkId); break; case 'replace': console.log("Opening replace modal for check:", checkId); await this.handleReplaceAction(checkId); break; case 'deliver': case 'pay': await this.updateCheckStatus(checkId, action); break; case 'print': console.log("Printing check:", checkId); await this.updateCheckStatus(checkId); break; } }, async handleCancel() { console.log("Cancel button:", $('#confirm-cancel').length); console.log("Cancel reason field:", $('#cancellation-reason').length); const checkId = $('#confirm-cancel').data('check-id'); const reason = $('#cancellation-reason').val(); if (!reason) { alert('Please provide a cancellation reason'); return; } try { const response = await fetch(`/testapp/checks/${checkId}/action/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify({ action: 'cancel', reason: reason }) }); if (!response.ok) throw new Error('Failed to cancel check'); $('#cancelModal').modal('hide'); $('#cancellation-reason').val(''); await this.applyFilters(); await this.showCheckDetails(checkId); } catch (error) { console.error('Error cancelling check:', error); alert('Failed to cancel check: ' + error.message); } }, async handleReject() { const checkId = $('#confirm-reject').data('check-id'); const reason = $('#rejection-reason').val(); const notes = $('#rejection-notes').val(); if (!reason) { alert('Please select a rejection reason'); return; } try { const response = await fetch(`/testapp/checks/${checkId}/action/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify({ action: 'reject', rejection_reason: reason, rejection_note: notes }) }); if (!response.ok) throw new Error('Failed to reject check'); $('#rejectModal').modal('hide'); $('#rejection-reason').val(''); $('#rejection-notes').val(''); await this.applyFilters(); await this.showCheckDetails(checkId); } catch (error) { console.error('Error rejecting check:', error); alert('Failed to reject check: ' + error.message); } }, async handleReceiveAction() { const checkId = $('#confirm-receive').data('check-id'); const notes = $('#receive-notes').val(); try { const response = await fetch(`/testapp/checks/${checkId}/action/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify({ action: 'receive', notes: notes }) }); if (!response.ok) throw new Error('Failed to receive check'); $('#receiveModal').modal('hide'); $('#receive-notes').val(''); await this.applyFilters(); await this.showCheckDetails(checkId); } catch (error) { console.error('Error receiving check:', error); alert('Failed to receive check: ' + error.message); } }, async handleReplaceAction(checkId) { try { // Load available checkers const checkerResponse = await fetch('/testapp/checkers/available/'); if (!checkerResponse.ok) throw new Error('Failed to fetch available checkers'); const checkerData = await checkerResponse.json(); // Populate checker dropdown const select = $('#replacement-checker'); select.empty().append('<option value="">Select a checker...</option>'); checkerData.checkers.forEach(checker => { select.append(`<option value="${checker.id}">${checker.label}</option>`); }); // Load check details const checkResponse = await fetch(`/testapp/checks/${checkId}/details/`); if (!checkResponse.ok) throw new Error('Failed to fetch check details'); const checkData = await checkResponse.json(); // Populate form $('#originalCheckRef').text(checkData.reference); $('#replacement-amount').val(checkData.amount); // Set default due date to today+30 const defaultDueDate = new Date(); defaultDueDate.setDate(defaultDueDate.getDate() + 30); $('#replacement-due-date').val(defaultDueDate.toISOString().split('T')[0]); // Show modal and store check ID $('#replacementModal').modal('show'); $('#create-replacement').data('original-check-id', checkId); } catch (error) { console.error('Error preparing replacement:', error); alert('Failed to prepare replacement: ' + error.message); } }, async handleCreateReplacement() { const checkId = $('#create-replacement').data('original-check-id'); const data = { action: 'replace', checker_id: $('#replacement-checker').val(), amount: $('#replacement-amount').val(), payment_due: $('#replacement-due-date').val(), observation: $('#replacement-observation').val() }; if (!data.checker_id) { alert('Please select a checker'); return; } try { const response = await fetch(`/testapp/checks/${checkId}/action/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); if (!response.ok) throw new Error('Failed to create replacement'); $('#replacementModal').modal('hide'); await this.applyFilters(); } catch (error) { console.error('Error creating replacement:', error); alert('Failed to create replacement: ' + error.message); } }, async updateCheckStatus(checkId, action) { try { const response = await fetch(`/testapp/checks/${checkId}/action/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify({ action }) }); if (!response.ok) throw new Error('Failed to update check status'); this.applyFilters(); } catch (error) { console.error('Error updating check status:', error); alert('Failed to update check status: ' + error.message); } }, async showCheckDetails(checkId) { try { const response = await fetch(`/testapp/checks/${checkId}/details/`); if (!response.ok) throw new Error('Failed to fetch check details'); const data = await response.json(); console.log("Check details data:", data); this.updateStatusModal(data); $('#statusInfoModal').modal('show'); } catch (error) { console.error('Error loading check details:', error); alert('Failed to load check details'); } }, updateStatusModal(data) { let content = `<div class="timeline">`; // Creation content += this.createTimelineEntry('Created', data.creation_date, 'plus', 'info'); // Show if this check replaces another if (data.replacement_info.replaces) { const replaces = data.replacement_info.replaces; content += this.createTimelineEntry( 'Replaces Check', replaces.rejection_date, 'sync', 'info', `<p>Replaces: ${replaces.reference}</p> <p>Original Amount: ${formatMoney(replaces.amount)}</p> <p>Rejection Reason: ${replaces.rejection_reason}</p>` ); } // Delivered if (data.delivered_at) { content += this.createTimelineEntry('Delivered', data.delivered_at, 'truck', 'primary'); } // Paid if (data.paid_at) { content += this.createTimelineEntry('Paid', data.paid_at, 'check', 'success'); } // Rejected if (data.rejected_at) { content += this.createTimelineEntry('Rejected', data.rejected_at, 'times', 'warning', `<p><strong>Reason:</strong> ${data.rejection_reason}</p> ${data.rejection_note ? `<p><strong>Note:</strong> ${data.rejection_note}</p>` : ''}` ); } // Show received status if applicable if (data.received_at) { content += this.createTimelineEntry( 'Received Back', data.received_at, 'hand-holding', 'info', data.received_notes ? `<p><strong>Notes:</strong> ${data.received_notes}</p>` : '' ); } // Show replacement if exists if (data.replacement_info.replaced_by) { const replacement = data.replacement_info.replaced_by; content += this.createTimelineEntry( 'Replaced', replacement.date, 'sync', 'success', `<p><strong>New Check:</strong> ${replacement.reference}</p> <p><strong>Amount:</strong> ${formatMoney(replacement.amount)}</p>` ); } // Cancelled if (data.cancelled_at) { content += this.createTimelineEntry('Cancelled', data.cancelled_at, 'ban', 'danger', `<p><strong>Reason:</strong> ${data.cancellation_reason}</p>` ); } content += '</div>'; $('#statusInfoModal .modal-body').html(content); }, createTimelineEntry(title, date, icon, color, extraContent = '') { return ` <div class="timeline-item"> <div class="timeline-badge bg-${color}"> <i class="fas fa-${icon} text-white"></i> </div> <div class="timeline-content"> <h6>${title}</h6> <p>${date}</p> ${extraContent} </div> </div> `; } }; // Initialize filters $(document).ready(() => { CheckFilters.init(); // Toggle filter panel $('#toggle-filters').click(function() { $('.filter-panel').slideToggle(); $(this).find('i').toggleClass('fa-filter fa-filter-slash'); }); }); </script> {% endblock %}
```

# templates/checker/checker_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Checkers</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#checkerModal"> <i class="fas fa-plus"></i> New Checker </button> </div> <!-- Filters --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-3"> <select class="form-control" id="bankFilter"> <option value="">All Banks</option> {% for account in banks %} <option value="{{ account.id }}"> {{ account.bank }} [{{ account.account_number }}] </option> {% endfor %} </select> </div> <div class="col-md-3"> <select class="form-control" id="typeFilter"> <option value="">All Types</option> <option value="CHQ">Cheque</option> <option value="LCN">LCN</option> </select> </div> <div class="col-md-3"> <select class="form-control" id="statusFilter"> <option value="">All Status</option> <option value="new">New</option> <option value="in_use">In Use</option> <option value="completed">Completed</option> </select> </div> <div class="col-md-3"> <input type="text" class="form-control" id="searchChecker" placeholder="Search code or index..."> </div> </div> </div> </div> <!-- Checkers Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Code</th> <th>Bank Account</th> <th>Type</th> <th>Index Range</th> <th>Current Position</th> <th>Status</th> <th>Created</th> <th>Actions</th> </tr> </thead> <tbody id="checkersTableBody"> {% include 'checker/partials/checkers_table.html' %} </tbody> </table> </div> </div> <!-- Checker Modal --> <div class="modal fade" id="checkerModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Create New Checker</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="row"> <div class="col-md-6"> <div class="col-md-6"> <div class="form-group"> <label>Bank Account</label> <input type="text" class="form-control" id="bankAccount" placeholder="Search bank account..."> <input type="hidden" id="selected-bank-id"> <div class="invalid-feedback">Required</div> </div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Type</label> <select class="form-control" id="checkerType"> <option value="CHQ">Cheque</option> <option value="LCN">LCN</option> </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Number of Pages</label> <select class="form-control" id="numPages"> <option value="25">25</option> <option value="50">50</option> <option value="100">100</option> </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Index</label> <input type="text" class="form-control" id="checkerIndex" maxlength="3" style="text-transform: uppercase;"> <div class="invalid-feedback">1-3 uppercase letters only</div> </div> </div> <div class="col-12"> <div class="form-group"> <label>Starting Page</label> <input type="number" class="form-control" id="startingPage" min="1"> <div class="invalid-feedback">Must be greater than 0</div> </div> </div> <div class="preview-section mt-3 d-none"> <div class="alert alert-info"> Preview: <strong id="checkerPreview"></strong> </div> </div> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveChecker" disabled>Create</button> </div> </div> </div> </div> <!-- Payment Modal --> <div class="modal fade" id="paymentModal" tabindex="-1" role="dialog"> <div class="modal-dialog" role="document"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Add Payment</h5> <button type="button" class="close" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <!-- Payment Summary Cards --> <div class="row mb-4"> <div class="col-md-6"> <div class="card bg-light"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Invoice Total</h6> <h4 id="invoice-total" class="card-title mb-0">-</h4> </div> </div> </div> <div class="col-md-6"> <div class="card bg-light"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Already Issued</h6> <h4 id="already-issued" class="card-title mb-0">-</h4> </div> </div> </div> </div> <div class="row mb-4"> <div class="col-md-6"> <div class="card bg-light"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Amount Paid</h6> <h4 id="amount-paid" class="card-title mb-0">-</h4> </div> </div> </div> <div class="col-md-6"> <div class="card bg-light"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Amount Available</h6> <h4 id="amount-available" class="card-title mb-0">-</h4> </div> </div> </div> </div> <form id="payment-form"> <input type="hidden" id="checker_id" name="checker_id"> <div class="form-group"> <label>Position</label> <input type="text" class="form-control" id="position" disabled> </div> <div class="form-group"> <label>Creation Date</label> <input type="date" class="form-control" name="creation_date" value="{% now 'Y-m-d' %}"> </div> <div class="form-group"> <label>Beneficiary</label> <input type="text" class="form-control" id="beneficiary" placeholder="Search supplier..."> <input type="hidden" id="supplier_id"> </div> <div class="form-group"> <label>Invoice</label> <input type="text" class="form-control" id="invoice" placeholder="Search invoice..." disabled> <input type="hidden" id="invoice_id" name="invoice_id"> </div> <div class="form-group"> <label>Amount</label> <input type="number" class="form-control" name="amount" step="0.01" required> <div class="invalid-feedback"> Amount cannot exceed the available amount for payment. </div> </div> <div class="form-group"> <label>Payment Due Date</label> <input type="date" class="form-control" name="payment_due"> </div> <div class="form-group"> <label>Observation</label> <textarea class="form-control" name="observation"></textarea> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> <button type="button" class="btn btn-success" id="save-and-clone">Save and Clone</button> <button type="button" class="btn btn-primary" id="save-payment">Save</button> </div> </div> </div> </div> <div class="modal fade" id="checkActionModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Check Action</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="check-details mb-4"> <div class="row"> <div class="col-6"> <small class="text-muted">Reference</small> <h5 id="checkRef"></h5> </div> <div class="col-6 text-right"> <small class="text-muted">Amount</small> <h5 id="checkAmount"></h5> </div> </div> </div> <div class="action-section"> <div class="form-group"> <label>Action</label> <select class="form-control" id="checkAction"> <option value="deliver">Deliver</option> <option value="pay">Mark as Paid</option> <option value="reject">Reject</option> <option value="replace">Replace</option> </select> </div> <!-- Rejection Fields --> <div id="rejectionFields" style="display: none;"> <div class="form-group"> <label>Rejection Reason</label> <select class="form-control" id="rejectionReason"> <option value="insufficient_funds">Insufficient Funds</option> <option value="signature_mismatch">Signature Mismatch</option> <option value="amount_error">Amount Error</option> <option value="date_error">Date Error</option> <option value="other">Other</option> </select> </div> <div class="form-group"> <label>Rejection Note</label> <textarea class="form-control" id="rejectionNote" rows="3"></textarea> </div> </div> <!-- Replacement Fields --> <div id="replacementFields" style="display: none;"> <div class="alert alert-info"> This will create a new check with the same details. You can modify the amount and date in the next step. </div> </div> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="confirmAction">Confirm</button> </div> </div> </div> </div> <!-- Replacement Modal --> <div class="modal fade" id="replacementModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Create Replacement Check</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="alert alert-warning"> <strong>Replacing check:</strong> <span id="oldCheckRef"></span> </div> <div class="form-group"> <label>Amount</label> <input type="number" class="form-control" id="newAmount" step="0.01"> </div> <div class="form-group"> <label>Payment Due Date</label> <input type="date" class="form-control" id="newDueDate"> </div> <div class="form-group"> <label>Observation</label> <textarea class="form-control" id="newObservation" rows="2"></textarea> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="createReplacement">Create</button> </div> </div> </div> </div> <style> .ui-autocomplete { position: absolute; z-index: 2000; /* Make sure it appears above the modal */ background-color: white; border: 1px solid #ccc; border-radius: 4px; padding: 5px 0; max-height: 200px; overflow-y: auto; list-style: none; } .ui-menu-item { padding: 8px 12px; cursor: pointer; } .ui-menu-item:hover { background-color: #f8f9fa; } .ui-helper-hidden-accessible { display: none; } </style> <script> const Utils = { formatMoney: (amount) => { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'MAD', minimumFractionDigits: 2 }).format(amount); }, showError: (message) => { const alert = $('<div>').addClass('alert alert-danger') .text(message) .prependTo('.modal-body'); setTimeout(() => alert.remove(), 5000); }, validateAmount: (amount, available) => { return amount > 0 && amount <= available; } }; const CheckerFilters = { init() { console.log("Initializing checker filters"); this.bankFilter = $('#bankFilter'); this.typeFilter = $('#typeFilter'); this.statusFilter = $('#statusFilter'); this.searchInput = $('#searchChecker'); this.setupAutocomplete(); this.bindEvents(); }, setupAutocomplete() { console.log("Setting up Autocomplete..."); // CSRF token for secure requests const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Initialize jQuery UI autocomplete this.bankInput.autocomplete({ source: async (request, response) => { try { const params = new URLSearchParams({ search: request.term }); const res = await fetch(`/testapp/bank-accounts/?${params}`, { headers: { 'X-CSRFToken': csrftoken, // Send CSRF token 'Content-Type': 'application/json' } }); if (!res.ok) throw new Error('Failed to fetch bank accounts'); const data = await res.json(); // Map response to expected autocomplete format response(data.map(account => ({ label: `${account.bank} [${account.account_number}]`, value: account.id, bank: account.bank }))); } catch (error) { console.error('Autocomplete error:', error); } }, minLength: 2, // Minimum characters before autocomplete triggers select: (event, ui) => { event.preventDefault(); this.bankInput.val(ui.item.label); // Display selected bank account label $('#selected-bank-id').val(ui.item.value); // Store selected bank ID this.validateForm(); // Re-validate form this.updatePreview(); // Update preview } }); console.log("Autocomplete initialized"); }, bindEvents() { // Instant filter on select changes this.bankFilter.on('change', () => this.applyFilters()); this.typeFilter.on('change', () => this.applyFilters()); this.statusFilter.on('change', () => this.applyFilters()); // Debounced search let timeout; this.searchInput.on('input', () => { clearTimeout(timeout); timeout = setTimeout(() => this.applyFilters(), 300); }); }, async applyFilters() { console.log("Applying filters"); const filters = { bank_account: this.bankFilter.val(), type: this.typeFilter.val(), status: this.statusFilter.val(), search: this.searchInput.val() }; console.log("Filter values:", filters); try { const response = await fetch(`/testapp/checkers/filter/?${new URLSearchParams(filters)}`); if (!response.ok) throw new Error('Filter request failed'); const data = await response.json(); $('#checkersTableBody').html(data.html); } catch (error) { console.error('Filter error:', error); } } }; const CheckerModal = { init() { this.modal = $('#checkerModal'); this.form = this.modal.find('form'); this.saveBtn = $('#saveChecker'); this.bankInput = $('#bankAccount'); console.log("Initializing CheckerModal..."); console.log("BankAccount input field found:", this.bankInput); this.setupAutocomplete(); this.setupValidation(); this.bindEvents(); }, setupAutocomplete() { console.log("Setting up Autocomplete..."); const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value; this.bankInput.autocomplete({ source: async (request, response) => { try { const params = new URLSearchParams({ search: request.term }); const res = await fetch(`/testapp/bank-accounts/?${params}`, { headers: { 'X-CSRFToken': csrftoken, // CSRF token for secure requests 'Content-Type': 'application/json' } }); if (!res.ok) throw new Error('Failed to fetch bank accounts'); const data = await res.json(); // Map response to the expected autocomplete format response(data.map(account => ({ label: `${account.bank} [${account.account_number}]`, value: account.id, bank: account.bank }))); } catch (error) { console.error('Autocomplete error:', error); } }, minLength: 2, select: (event, ui) => { event.preventDefault(); this.bankInput.val(ui.item.label); // Display selected bank account label $('#selected-bank-id').val(ui.item.value); // Store selected bank ID this.validateForm(); // Re-validate form this.updatePreview(); // Update preview } }); console.log("Autocomplete initialized"); }, setupValidation() { const indexInput = $('#checkerIndex'); const startInput = $('#startingPage'); // Validate when the bank account changes this.bankInput.on('autocompleteselect', () => this.validateForm()); // Trigger validation on autocomplete selection // Validate index input indexInput.on('input', function () { this.value = this.value.toUpperCase(); $(this).toggleClass('is-valid', /^[A-Z]{1,3}$/.test(this.value)); CheckerModal.validateForm(); CheckerModal.updatePreview(); }); // Validate starting page input startInput.on('input', function () { $(this).toggleClass('is-valid', parseInt(this.value) > 0); CheckerModal.validateForm(); CheckerModal.updatePreview(); }); }, validateForm() { const isValid = $('#selected-bank-id').val() && // Ensure a bank account is selected /^[A-Z]{1,3}$/.test($('#checkerIndex').val()) && // Validate index parseInt($('#startingPage').val()) > 0; // Validate starting page this.saveBtn.prop('disabled', !isValid); // Enable or disable the save button return isValid; }, updatePreview() { const bank = this.bankInput.val(); // Get the bank label const index = $('#checkerIndex').val(); const start = $('#startingPage').val(); const pages = $('#numPages').val(); if (bank && index && start) { const end = parseInt(start) + parseInt(pages) - 1; $('#checkerPreview').text(`${bank}-${index}${start} to ${bank}-${index}${end}`); $('.preview-alert').removeClass('d-none'); } }, async saveChecker() { if (!this.validateForm()) return; try { const response = await fetch('/testapp/checkers/create/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() }, body: JSON.stringify({ bank_account_id: this.bankSelect.val(), type: $('#checkerType').val(), num_pages: $('#numPages').val(), index: $('#checkerIndex').val(), starting_page: $('#startingPage').val() }) }); if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'Creation failed'); } location.reload(); } catch (error) { Utils.showError(error.message); } }, bindEvents() { this.saveBtn.off("click").on('click', () => this.saveChecker()); this.modal.on('hidden.bs.modal', () => { if (this.form.length > 0) { this.form[0].reset(); // Reset only if the form exists } this.bankSelect.val(null).trigger('change'); $('.preview-alert').addClass('d-none'); }); this.modal.on('shown.bs.modal', () => { console.log("Modal opened. Checking dropdown options:"); console.log(this.bankSelect.find('option')); // Confirm options are there }); } }; $(document).ready(() => { CheckerModal.init(); CheckerFilters.init(); }); </script> {% endblock %}
```

# templates/checker/partials/check_action_modals.html

```html
<!-- templates/checker/partials/check_action_modals.html --> <!-- Status Info Modal --> <div class="modal fade" id="statusInfoModal"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Check Status History</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Timeline will be inserted here --> </div> </div> </div> </div> <!-- Reject Modal --> <div class="modal fade" id="rejectModal"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Reject Assy Check</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="form-group"> <label>Rejection Reason</label> <select class="form-control" id="rejection-reason" required> <option value="">Select reason...</option> {% for value, label in rejection_reasons %} <option value="{{ value }}">{{ label }}</option> {% endfor %} </select> </div> <div class="form-group"> <label>Additional Notes</label> <textarea class="form-control" id="rejection-notes" rows="3"></textarea> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> <button type="button" class="btn btn-danger" id="confirm-reject">Confirm Rejection</button> </div> </div> </div> </div> <!-- Cancel Modal --> <div class="modal fade" id="cancelModal"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Cancel Check</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="form-group"> <label>Cancellation Reason</label> <textarea class="form-control" id="cancellation-reason" rows="3" required></textarea> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> <button type="button" class="btn btn-danger" id="confirm-cancel">Confirm Cancellation</button> </div> </div> </div> </div> <!-- Replacement Modal --> <div class="modal fade" id="replacementModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Replace Check Baby!!</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="alert alert-info"> <strong>Original Check:</strong> <span id="originalCheckRef"></span> </div> <form id="replacement-form"> <div class="form-group"> <label>Select Checker</label> <select class="form-control" id="replacement-checker" required> <option value="">Select a checker...</option> </select> <small class="text-muted">Shows available pages in parentheses</small> </div> <div class="form-group"> <label>Amount</label> <input type="number" class="form-control" id="replacement-amount" step="0.01" required> </div> <div class="form-group"> <label>Payment Due Date</label> <input type="date" class="form-control" id="replacement-due-date"> </div> <div class="form-group"> <label>Observation</label> <textarea class="form-control" id="replacement-observation" rows="2"></textarea> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="create-replacement">Create Replacement</button> </div> </div> </div> </div> <!-- Receive Check Modal --> <div class="modal fade" id="receiveModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Receive Check</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="form-group"> <label>Notes</label> <textarea class="form-control" id="receive-notes" rows="3" placeholder="Add any notes about receiving this check..."></textarea> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="confirm-receive">Confirm Receipt</button> </div> </div> </div> </div>
```

# templates/checker/partials/checkers_table.html

```html
{% load custom_filters %} <!-- checkers_table.html --> {% for checker in checkers %} <tr> <td> <span class="font-monospace">{{ checker.code }}</span> </td> <td> <div class="d-flex align-items-center"> <span class="bank-logo {{ checker.bank_account.bank|lower }}"></span> <span class="ml-2"> {{ checker.bank_account.bank }} [{{ checker.bank_account.account_number }}] </span> </div> </td> <td>{{ checker.get_type_display }}</td> <td> [{{ checker.index }}] {{ checker.starting_page }} - {{ checker.final_page }} <small class="text-muted"> <div class="progress-container" style="display: flex; align-items: center; gap: 10px;"> <div class="progress" style="height: 20px; width: 100px;"title="Remaining checkers: {{ checker.remaining_pages }}"> <div class="progress-bar {% if checker.remaining_percentage < 20 %}bg-danger{% elif checker.remaining_percentage < 50 %}bg-warning{% else %}bg-success{% endif %}" role="progressbar" style="width: {{ checker.remaining_percentage }}%;" aria-valuenow="{{ checker.remaining_percentage }}" aria-valuemin="0" aria-valuemax="100"> {{ checker.remaining_ratio }} </div> </div> {% if checker.remaining_percentage < 25 %} <span class="exclamation" title="Low remaining pages!">⚠️</span> {% endif %} </div> </small> </td> <td> <div class="position-info"> {{ checker.index }} {{ checker.current_position }} <div class="progress" style="height: 4px;"> <div class="progress-bar" role="progressbar" style="width: {{ checker.get_progress_percentage }}%"> </div> </div> </div> </td> <td> {% with status=checker.get_status %} <span class="badge badge-{{ status.color }}"> {{ status.label }} </span> {% endwith %} </td> <td>{{ checker.created_at|date:"d/m/Y" }}</td> <td class="actions"> {% if checker.status != 'completed' and checker.is_active %} <div class="btn-group"> <button class="btn btn-sm btn-info view-signatures" data-checker="{{ checker.id }}" data-start="{{ checker.starting_page }}" data-end="{{ checker.final_page }}"> <i class="fas fa-signature"></i> </button> <button class="btn btn-sm btn-success add-payment" data-checker="{{ checker.id }}" data-start="{{ checker.starting_page }}" data-end="{{ checker.final_page }}" data-position="{{ checker.current_position }}" data-bank="{{ checker.bank_account.bank }}" data-type="{{ checker.type }}"> <i class="fas fa-money-check-alt"></i> Add Payment </button> </div> {% endif %} </td> </tr> {% endfor %} <!-- Updated Payment Modal --> <div class="modal fade" id="paymentModal"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <span id="payment-checker-info"></span> </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Payment Summary Cards --> <div class="row mb-4"> <div class="col-md-3"> <div class="card bg-light"> <div class="card-body"> <h6 class="text-muted">Invoice Total</h6> <h4 id="invoice-total" class="mb-0">-</h4> </div> </div> </div> <div class="col-md-3"> <div class="card bg-light"> <div class="card-body"> <h6 class="text-muted">Already Issued</h6> <h4 id="already-issued" class="mb-0">-</h4> </div> </div> </div> <div class="col-md-3"> <div class="card bg-light"> <div class="card-body"> <h6 class="text-muted">Amount Paid</h6> <h4 id="amount-paid" class="mb-0">-</h4> </div> </div> </div> <div class="col-md-3"> <div class="card bg-light"> <div class="card-body"> <h6 class="text-muted">Available</h6> <h4 id="amount-available" class="mb-0 text-success">-</h4> </div> </div> </div> </div> <form id="payment-form"> {% csrf_token %} <input type="hidden" id="checker_id" name="checker_id"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="position">Position</label> <div class="input-group"> <input type="number" class="form-control" id="position" name="position"> <div class="input-group-append"> <div id="signature-badges" class="input-group-text"></div> </div> </div> <div class="invalid-feedback"></div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Creation Date</label> <input type="date" class="form-control" name="creation_date" value="{% now 'Y-m-d' %}"> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Beneficiary</label> <input type="text" class="form-control" id="beneficiary" placeholder="Search supplier..."> <input type="hidden" id="supplier_id"> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Invoice</label> <input type="text" class="form-control" id="invoice" placeholder="Search invoice..." disabled> <input type="hidden" id="invoice_id" name="invoice_id"> </div> </div> </div> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label>Amount</label> <input type="number" class="form-control" name="amount" step="0.01" required> <div class="invalid-feedback"></div> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Payment Due Date</label> <input type="date" class="form-control" name="payment_due"> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Observation</label> <textarea class="form-control" name="observation" rows="1"></textarea> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-success" id="save-and-clone"> <i class="fas fa-copy"></i> Save & Clone </button> <button type="button" class="btn btn-primary" id="save-payment"> <i class="fas fa-save"></i> Save </button> </div> </div> </div> </div> <!-- Signature Modal --> <div class="modal fade" id="signatureModal"> <div class="modal-dialog modal-xl"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Checker Signatures</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="table-responsive"> <table class="table"> <thead> <tr> <th>Position</th> <th>Status</th> <th>Signatures</th> <th>Actions</th> </tr> </thead> <tbody id="signature-positions"> </tbody> </table> </div> </div> </div> </div> </div> <script> function formatMoney(amount) { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'MAD', minimumFractionDigits: 2 }).format(amount); } const PaymentValidation = { setupPositionValidation() { console.log("Setting up position validation"); const positionInput = $('[name="position"]'); let lastValidPosition = this.currentCheckerData?.next_available; console.log("Initial lastValidPosition:", lastValidPosition); // Real-time validation on input positionInput.on('input', async (e) => { const position = parseInt(e.target.value); console.log("Position changed:", { value: position, start: this.currentCheckerData?.start, end: this.currentCheckerData?.end, currentPosition: this.currentCheckerData?.position }); if (!this.currentCheckerData) { console.error("No checker data available"); return; } // Check range and used positions const isValid = await this.validatePosition(position); console.log("Position validation result:", isValid); if (isValid) { lastValidPosition = position; await this.loadSignatureInfo(this.currentCheckerData.id, position); } }); // Revert to last valid position on blur positionInput.on('blur', function() { if ($(this).hasClass('is-invalid')) { console.log("Reverting to last valid position:", lastValidPosition); $(this).val(lastValidPosition); $(this).removeClass('is-invalid'); } }); }, async validatePosition(position) { const input = $('[name="position"]'); const feedback = input.siblings('.invalid-feedback'); console.log("Validating position:", { position, start: this.currentCheckerData.start, end: this.currentCheckerData.end }); // Basic validation if (!position) { this.setPositionInvalid("Position is required", input, feedback); return false; } // Range validation if (position < this.currentCheckerData.start || position > this.currentCheckerData.end) { this.setPositionInvalid( `Position must be between ${this.currentCheckerData.start} and ${this.currentCheckerData.end}`, input, feedback ); return false; } // Check if position is already used try { const response = await fetch( `/testapp/checkers/${this.currentCheckerData.id}/position-status/${position}/` ); const data = await response.json(); console.log("Position status check result:", data); if (data.is_used) { this.setPositionInvalid( `Position ${position} is already used`, input, feedback ); return false; } } catch (error) { console.error("Error checking position status:", error); return false; } input.removeClass('is-invalid').addClass('is-valid'); return true; }, setPositionInvalid(message, input, feedback) { console.log("Setting position invalid:", message); input.removeClass('is-valid').addClass('is-invalid'); feedback.text(message); $('#signature-badges').empty(); } }; const PaymentSystem = { init() { Object.assign(this, PaymentValidation); this.modal = $('#paymentModal'); this.form = $('#payment-form'); this.beneficiaryInput = $('#beneficiary'); this.invoiceInput = $('#invoice'); this.amountInput = $('[name="amount"]'); this.currentCheckerData = null; this.setupValidation(); this.setupPositionValidation(); this.setupAutoComplete(); this.setupValidation(); this.bindEvents(); }, async loadSignatureInfo(checkerId, position) { console.log(`Loading signature info for position ${position}`); try { const response = await fetch(`/testapp/checkers/${checkerId}/signatures/?position=${position}`); const data = await response.json(); console.log("Signature data:", data); const badges = $('#signature-badges'); badges.empty(); const posInfo = data.positions[position] || { signatures: [], timestamps: [] }; posInfo.signatures.forEach((sig, idx) => { badges.append(` <span class="badge badge-primary ml-1" title="Signed on ${new Date(posInfo.timestamps[idx]).toLocaleDateString()}"> ${sig} </span> `); }); } catch (error) { console.error("Error loading signature info:", error); } }, setPositionInvalid(message, input, feedback) { input.removeClass('is-valid').addClass('is-invalid'); feedback.text(message); $('#signature-badges').empty(); }, setupAutoComplete() { // Beneficiary Autocomplete this.beneficiaryInput.autocomplete({ minLength: 2, appendTo: this.modal, source: async (request, response) => { try { const data = await $.get('/testapp/suppliers/autocomplete/', { term: request.term }); response(data.map(item => ({ label: item.label, value: item.value }))); } catch (error) { console.error('Supplier fetch failed:', error); response([]); } }, select: (_, ui) => { $('#supplier_id').val(ui.item.value); this.beneficiaryInput.val(ui.item.label.split(' (')[0]); this.invoiceInput.prop('disabled', false).val(''); $('#invoice_id').val(''); this.resetPaymentInfo(); return false; }, change: (event, ui) => { if (!ui.item) { this.beneficiaryInput.val(''); $('#supplier_id').val(''); this.invoiceInput.prop('disabled', true).val(''); $('#invoice_id').val(''); this.resetPaymentInfo(); } } }); // Invoice Autocomplete this.invoiceInput.autocomplete({ minLength: 2, appendTo: this.modal, source: async (request, response) => { const supplierId = $('#supplier_id').val(); if (!supplierId) return response([]); try { const data = await $.get('/testapp/invoices/autocomplete/', { term: request.term, supplier: supplierId }); response(data.map(item => ({ label: `${item.ref} (${item.date}) - ${item.status}`, value: item.id, payment_info: item.payment_info, ref: item.ref }))); } catch (error) { console.error('Invoice fetch failed:', error); response([]); } }, select: (_, ui) => { this.handleInvoiceSelect(ui.item); return false; }, change: (event, ui) => { if (!ui.item) { this.invoiceInput.val(''); $('#invoice_id').val(''); $('#invoice-total, #already-issued, #amount-paid, #amount-available').text('-'); this.amountInput.val('').removeClass('is-invalid'); $('#save-payment, #save-and-clone').prop('disabled', true); } } }); }, handleInvoiceSelect(item) { const info = item.payment_info; this.invoiceInput.val(item.ref); $('#invoice_id').val(item.value); // Update payment info cards $('#invoice-total').text(Utils.formatMoney(info.total_amount)); $('#already-issued').text(Utils.formatMoney(info.issued_amount)); $('#amount-paid').text(Utils.formatMoney(info.paid_amount)); $('#amount-available').text(Utils.formatMoney(info.available_amount)); // Set initial amount this.amountInput .val(info.available_amount.toFixed(2)) .removeClass('is-invalid') .trigger('input'); this.updateSaveButtons(true); this.updateSaveButtons( $('#supplier_id').val() && item.value && Utils.validateAmount(parseFloat(this.amountInput.val()), info.available_amount) ); }, resetPaymentInfo() { $('#invoice-total, #already-issued, #amount-paid, #amount-available').text('-'); this.amountInput.val('').removeClass('is-invalid'); this.updateSaveButtons(false); }, setupValidation() { let lastValidAmount = 0; this.amountInput.on('input blur', (e) => { const $input = $(e.target); const rawValue = $input.val(); // Get the raw input value console.log("Raw input value:", rawValue); // Debug console.log("Sanitized value:", rawValue); // Debug const amount = parseFloat(rawValue) || 0; // Parse sanitized input console.log("Parsed amount:", amount); // Debug const availableText = $('#amount-available').text(); const available = parseFloat( availableText .replace(/[^0-9,-]+/g, '') // Clean non-numeric characters .replace(/\s|(?<=\d)\./g, '') // Remove thousand separators .replace(',', '.') // Normalize decimal separator ) || 0; console.log("Available amount (parsed):", available); // Debug if (e.type === 'input') { if (amount <= 0) { // Real-time feedback for zero or negative values $input.addClass('is-invalid'); $('.invalid-feedback').text('Amount must be greater than 0'); $('#save-payment').prop('disabled', true); } else if (amount > available) { // Real-time feedback for exceeding available amount $input.addClass('is-invalid'); $('.invalid-feedback').text(`Amount cannot exceed ${formatMoney(available)}`); $('#save-payment').prop('disabled', true); } else { // Valid input $input.removeClass('is-invalid'); $('.invalid-feedback').empty(); $('#save-payment').prop('disabled', false); lastValidAmount = amount; // Update last valid amount } } else if (e.type === 'blur') { // On blur, revert to last valid amount if input is invalid if (amount <= 0 || amount > available) { console.log("Reverting to last valid amount:", lastValidAmount); // Debug $input.val(lastValidAmount.toFixed(2)); // Reset input $input.removeClass('is-invalid'); $('#save-payment').prop('disabled', false); } } }); }, updateSaveButtons(enabled) { $('#save-payment, #save-and-clone').prop('disabled', !enabled); }, async openPaymentModal(checkerData) { console.log("Opening payment modal with data:", checkerData); try { // First get checker details const response = await fetch(`/testapp/checkers/${checkerData.id}/details/`); const checkerDetails = await response.json(); console.log("Checker details:", checkerDetails); console.log("Checker details next available:", checkerDetails.next_available); if (!checkerDetails.next_available) { alert("No available positions in this checker"); return; } // Set up the checker data AFTER we have details this.currentCheckerData = { id: checkerData.id, start: checkerDetails.starting_page, end: checkerDetails.final_page, position: checkerDetails.next_available, bank: checkerData.bank, type: checkerData.type }; // Reset form first // Now set position explicitly $('#position').val(this.currentCheckerData.position); // Show modal last this.modal.modal('show'); // Trigger validation after modal is shown $('#position').trigger('input'); } catch (error) { console.error("Error opening payment modal:", error); alert("Error loading checker details"); } }, setPositionInvalid(message, input, feedback) { console.log("Setting position invalid:", message); input.removeClass('is-valid').addClass('is-invalid'); feedback.text(message); $('#signature-badges').empty(); }, resetForm() { this.form[0].reset(); this.beneficiaryInput.val(''); this.invoiceInput.val('').prop('disabled', true); $('#supplier_id, #invoice_id').val(''); this.resetPaymentInfo(); this.amountInput.removeClass('is-invalid'); $('[name="creation_date"]').val(new Date().toISOString().split('T')[0]); // Preserve the position value if (this.currentCheckerData?.position) { $('#position').val(this.currentCheckerData.position); } }, resetPaymentInfo() { $('#invoice-total, #already-issued, #amount-paid, #amount-available').text('-'); this.amountInput.val('').removeClass('is-invalid'); this.updateSaveButtons(false); }, async createPayment(cloneAfter = false) { console.log("Creating payment with data:", { checker_id: this.currentCheckerData?.id, invoice_id: $('#invoice_id').val(), amount: $('[name="amount"]').val(), position: $('#position').val() }); const data = { checker_id: this.currentCheckerData.id, invoice_id: $('#invoice_id').val(), amount: $('[name="amount"]').val(), position: $('[name="position"]').val(), payment_due: $('[name="payment_due"]').val() || null, observation: $('[name="observation"]').val(), creation_date: $('[name="creation_date"]').val() }; try { const response = await fetch('/testapp/checks/create/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() }, body: JSON.stringify(data) }); if (!response.ok) throw new Error(await response.text()); if (cloneAfter) { const available = parseFloat($('#amount-available').text().replace(/[^\d.-]/g, '')); $('[name="amount"]').val(available.toFixed(2)).trigger('input'); } else { this.modal.modal('hide'); location.reload(); } } catch (error) { console.error("Error creating check:", error); } }, validateForm() { // Basic validation if (!$('#supplier_id').val()) { Utils.showError('Please select a supplier'); return false; } if (!$('#invoice_id').val()) { Utils.showError('Please select an invoice'); return false; } if (!this.amountInput.val() || this.amountInput.hasClass('is-invalid')) { Utils.showError('Please enter a valid amount'); return false; } return true; }, bindEvents() { // Open modal trigger $(document).on('click', '.add-payment', (e) => { const button = $(e.currentTarget); this.openPaymentModal({ id: button.data('checker'), bank: button.data('bank'), type: button.data('type'), position: button.data('position') }); }); // Save buttons $('#save-payment').on('click', () => this.createPayment(false)); $('#save-and-clone').on('click', () => this.createPayment(true)); // Modal cleanup this.modal.on('hidden.bs.modal', () => { this.resetForm(); this.currentCheckerData = null; }); } }; const SignatureSystem = { init() { this.modal = $('#signatureModal'); this.bindEvents(); }, bindEvents() { $(document).on('click', '.view-signatures', (e) => { const button = $(e.currentTarget); this.openSignatureModal({ id: button.data('checker'), start: button.data('start'), end: button.data('end') }); }); $(document).on('click', '.add-signature', (e) => { const btn = $(e.currentTarget); this.addSignature( btn.data('checker'), btn.data('position'), btn.data('signature') ); }); }, async loadPositions(checkerId, start, end) { console.log("Fetching signature data..."); try { const response = await fetch(`/testapp/checkers/${checkerId}/signatures/?start=${start}&end=${end}`); const data = await response.json(); console.log("Received signature data:", data); this.updateSignatureTable(data, checkerId, start, end); } catch (error) { console.error("Error loading signatures:", error); } }, updateSignatureTable(data, checkerId, start, end) { const tbody = $('#signature-positions'); tbody.empty(); for (let position = start; position <= end; position++) { const posInfo = data.positions[position] || { signatures: [], timestamps: [] }; const isUsed = data.used_positions.hasOwnProperty(position); tbody.append(this.createPositionRow(position, posInfo, isUsed, checkerId)); } }, createPositionRow(position, posInfo, isUsed, checkerId) { const row = $('<tr>'); row.append(`<td>${position}</td>`); row.append(`<td>${isUsed ? 'Used' : 'Available'}</td>`); row.append(this.createSignaturesBadges(posInfo)); if (!isUsed) { row.append(this.createSignatureButtons(position, posInfo, checkerId)); } else { row.append('<td></td>'); } return row; }, createSignaturesBadges(posInfo) { const badges = posInfo.signatures.map((sig, idx) => `<span class="badge badge-primary mr-1" title="${posInfo.timestamps[idx]}">${sig}</span>` ).join(''); return $('<td>').html(badges); }, createSignatureButtons(position, posInfo, checkerId) { const td = $('<td>'); if (!posInfo.signatures.includes('OUK')) { td.append(this.createSignatureButton('OUK', checkerId, position)); } if (!posInfo.signatures.includes('KEZ')) { td.append(this.createSignatureButton('KEZ', checkerId, position)); } return td; }, createSignatureButton(signature, checkerId, position) { return $(` <button class="btn btn-sm btn-outline-primary mr-1 add-signature" data-checker="${checkerId}" data-position="${position}" data-signature="${signature}"> Sign ${signature} </button> `); }, async addSignature(checkerId, position, signature) { console.log(`Adding signature ${signature} to position ${position}`); try { const formData = new FormData(); formData.append('position', position); formData.append('signature', signature); const response = await fetch(`/testapp/checkers/${checkerId}/sign/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: formData }); if (!response.ok) throw new Error('Signature failed'); await this.loadPositions( checkerId, this.currentStart, this.currentEnd ); } catch (error) { console.error("Error adding signature:", error); } }, openSignatureModal(checkerData) { this.currentStart = checkerData.start; this.currentEnd = checkerData.end; this.loadPositions(checkerData.id, checkerData.start, checkerData.end); this.modal.modal('show'); } }; // Initialize everything $(document).ready(() => { CheckerModal.init(); CheckerFilters.init(); PaymentSystem.init(); SignatureSystem.init(); }); </script>
```

# templates/checker/partials/checks_table.html

```html
<!-- checker/partials/checks_table.html --> {% load check_tags %} {% for check in checks %} <tr class="{% if check.status == 'paid' %}table-success{% elif check.status == 'cancelled' %}table-danger{% elif check.status == 'rejected' %}table-warning{% elif check.status == 'delivered' %}table-info{% endif %}"> <td> <span class="font-monospace">{{ check.checker.bank_account.bank }}-{{ check.position }}</span> </td> <td> <div class="d-flex align-items-center"> <span class="bank-logo {{ check.checker.bank_account.bank|lower }}"></span> <span class="ml-2">{{ check.checker.bank_account.get_bank_display }}</span> </div> </td> <td>{{ check.creation_date|date:"Y-m-d" }}</td> <td>{{ check.beneficiary.name }}</td> <td>{{ check.cause.ref }}</td> <td class="text-right">{{ check.amount_due|floatformat:2 }}</td> <td class="text-right">{{ check.amount|floatformat:2 }}</td> <td>{{ check.payment_due|date:"Y-m-d"|default:"-" }}</td> <td> <span class="badge badge-{{ check.status|status_badge }} status-badge" data-check-id="{{ check.id }}" data-toggle="tooltip" title="Click for details"> <i class="fas fa-{% if check.status == 'paid' %}check-circle {% elif check.status == 'cancelled' %}ban {% elif check.status == 'rejected' %}times-circle {% elif check.status == 'delivered' %}truck {% else %}clock{% endif %}"></i> {{ check.get_status_display }} </span> </td> <td> <div class="btn-group"> {% if check.status == 'draft' %} <button class="btn btn-sm btn-info check-action" data-action="print" data-check-id="{{ check.id }}"> <i class="fas fa-print"></i> Print </button> {% elif check.status == 'ready_to_sign' %} <button class="btn btn-sm btn-primary check-action" data-action="sign" data-check-id="{{ check.id }}"> <i class="fas fa-signature"></i> Sign </button> <button class="btn btn-sm btn-danger check-action" data-action="cancel" data-check-id="{{ check.id }}"> <i class="fas fa-ban"></i> </button> {% elif check.status == 'pending' and not check.cancelled_at %} <button class="btn btn-sm btn-danger check-action" data-action="cancel" data-check-id="{{ check.id }}"> <i class="fas fa-ban"></i> </button> <button class="btn btn-sm btn-success check-action" data-action="deliver" data-check-id="{{ check.id }}"> <i class="fas fa-truck"></i> </button> {% elif check.status == 'delivered' and not check.cancelled_at %} <button class="btn btn-sm btn-danger check-action" data-action="cancel" data-check-id="{{ check.id }}"> <i class="fas fa-ban"></i> </button> <button class="btn btn-sm btn-warning check-action" data-action="reject" data-check-id="{{ check.id }}"> <i class="fas fa-times"></i> </button> <button class="btn btn-sm btn-success check-action" data-action="pay" data-check-id="{{ check.id }}"> <i class="fas fa-check"></i> </button> {% elif check.status == 'rejected' %} {% if check.is_received %} <button class="btn btn-sm btn-danger check-action" data-action="cancel" data-check-id="{{ check.id }}"> <i class="fas fa-ban"></i> </button> {% elif not check.is_received %} <button class="btn btn-sm btn-info check-action" data-action="receive" data-check-id="{{ check.id }}"> <i class="fas fa-hand-holding"></i> Receive </button> {% elif not check.has_replacement %} <button class="btn btn-sm btn-primary check-action" data-action="replace" data-check-id="{{ check.id }}"> <i class="fas fa-sync"></i> Replace </button> {% endif %} {% endif %} </div> </td> </tr> {% empty %} <tr> <td colspan="10" class="text-center py-4"> <div class="empty-state"> <i class="fas fa-search fa-3x text-muted mb-3"></i> <p class="text-muted mb-0">No checks found matching your criteria</p> {% if request.GET %} <button type="button" class="btn btn-link" id="clear-filters">Clear all filters</button> {% endif %} </div> </td> </tr> {% endfor %}
```

# templates/checker/partials/signature_modal.html

```html
<div class="modal fade" id="signatureModal"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Sign Checks</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="signature-controls mb-3"> <div class="btn-group"> <button class="btn btn-outline-primary signature-btn" data-signature="OUK"> Sign OUK </button> <button class="btn btn-outline-primary signature-btn" data-signature="KEZ"> Sign KEZ </button> </div> </div> <table class="table"> <thead> <tr> <th>Position</th> <th>Supplier</th> <th>Amount</th> <th>Status</th> <th>Signatures</th> <th>Actions</th> </tr> </thead> <tbody id="checksToSign"> </tbody> </table> </div> </div> </div> </div>
```

# templates/client/client_card.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ client.name }} - Client Card</h2> <!-- Period Selection --> <div class="d-flex gap-2"> <form class="form-inline" method="get"> <select name="year" class="form-control mr-2"> {% for year_choice in years %} <option value="{{ year_choice }}" {% if year_choice == selected_year %}selected{% endif %}> {{ year_choice }} </option> {% endfor %} </select> <select name="month" class="form-control mr-2"> {% for month_num, month_name in months %} <option value="{{ month_num }}" {% if month_num == selected_month %}selected{% endif %}> {{ month_name }} </option> {% endfor %} </select> <button type="submit" class="btn btn-primary">Apply</button> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Debit</h5> <p class="card-text text-danger h4">{{ total_debit|floatformat:2 }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Credit</h5> <p class="card-text text-success h4">{{ total_credit|floatformat:2 }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Balance</h5> <p class="card-text h4 {% if final_balance > 0 %}text-danger{% else %}text-success{% endif %}"> {{ final_balance|floatformat:2 }} </p> </div> </div> </div> </div> <!-- Transactions Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Description</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th class="text-right">Balance</th> </tr> </thead> <tbody> {% for t in transactions %} <tr {% if t.type == 'BALANCE' %}class="table-info"{% endif %}> <td>{{ t.date|date:"Y-m-d" }}</td> <td>{{ t.description }}</td> <td class="text-right text-danger"> {% if t.debit %}{{ t.debit|floatformat:2 }}{% endif %} </td> <td class="text-right text-success"> {% if t.credit %}{{ t.credit|floatformat:2 }}{% endif %} </td> <td class="text-right {% if t.balance > 0 %}text-danger{% else %}text-success{% endif %}"> {{ t.balance|floatformat:2 }} </td> </tr> {% empty %} <tr> <td colspan="5" class="text-center">No transactions found for this period</td> </tr> {% endfor %} </tbody> </table> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Auto-submit form when selection changes $('select[name="year"], select[name="month"]').change(function() { $(this).closest('form').submit(); }); }); </script> {% endblock %}
```

# templates/client/client_management.html

```html
{% extends 'base.html' %} {% load static %} {% block extra_css %} <link rel="stylesheet" href="{% static 'css/client.css' %}"> {% endblock %} {% block content %} <div class="container-fluid px-4"> <div class="row mt-4"> <div class="col"> <!-- Tabs Navigation --> <ul class="nav nav-tabs nav-fill border-0" id="clientTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active custom-tab" id="clients-tab" data-toggle="tab" href="#clients" role="tab"> <i class="fas fa-users me-2"></i>Clients </a> </li> <li class="nav-item"> <a class="nav-link custom-tab" id="entities-tab" data-toggle="tab" href="#entities" role="tab"> <i class="fas fa-building me-2"></i>Entities </a> </li> </ul> <!-- Tabs Content --> <div class="tab-content mt-4" id="clientTabsContent"> <!-- Clients Tab --> <div class="tab-pane fade show active" id="clients" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-users text-primary me-2"></i>Clients Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#clientModal"> <i class="fas fa-plus-circle me-2"></i>Add New Client </button> </div> <!-- Clients Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="clientsTable"> <thead class="bg-light"> <tr> <th>Client Code</th> <th>Name</th> <th>Created At</th> <th>Actions</th> </tr> </thead> <tbody id="clientsTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> <!-- Entities Tab --> <div class="tab-pane fade" id="entities" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-building text-primary me-2"></i>Entities Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#entityModal"> <i class="fas fa-plus-circle me-2"></i>Add New Entity </button> </div> <!-- Entities Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="entitiesTable"> <thead class="bg-light"> <tr> <th>Name</th> <th>ICE Code</th> <th>Accounting Code</th> <th>City</th> <th>Phone</th> <th>Actions</th> </tr> </thead> <tbody id="entitiesTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> </div> </div> </div> </div> {% include 'client/components/client_modal.html' %} {% include 'client/components/entity_modal.html' %} <script> console.log('Initializing client management module...'); // Validation configurations const ValidationConfig = { clientCode: { minLength: 5, maxLength: 10, pattern: /^\d+$/, messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 10 digits' } }, iceCode: { length: 15, pattern: /^\d+$/, inputPattern: /[0-9]/, // Add this - for single digit validation messages: { pattern: 'Only digits are allowed', length: 'Must be exactly 15 digits' } }, accountingCode: { minLength: 5, maxLength: 7, pattern: /^\d+$/, // Just check for digits initially messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 7 digits' } }, name: { pattern: /^[a-zA-Z\s]+$/, messages: { pattern: 'Only letters and spaces allowed' } } }; class FormValidator { constructor(formId, config) { this.form = document.getElementById(formId); this.config = config; console.log(`Initializing validator for form: ${formId}`); this.setupValidation(); } setupValidation() { const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { console.log(`Setting up validation for: ${input.id}`); this.setupInputValidation(input); }); } setupInputValidation(input) { const validationType = input.dataset.validate; const rules = this.config[validationType]; // Real-time validation input.addEventListener('input', (e) => { console.log(`Input event on ${input.id}`); this.validateInput(input, rules); }); // Blur validation input.addEventListener('blur', (e) => { console.log(`Blur event on ${input.id}`); this.validateInput(input, rules, true); }); // Prevent invalid characters input.addEventListener('keypress', (e) => { if (rules.pattern && !String.fromCharCode(e.charCode).match(rules.pattern)) { e.preventDefault(); } }); // Prevent invalid characters and enforce length input.addEventListener('keypress', (e) => { // Check max length for ICE code if (validationType === 'iceCode' && input.value.length >= 15) { e.preventDefault(); return; } // Special handling for first character of accounting code if (validationType === 'accountingCode') { if (input.value.length === 0 && e.key !== '3') { e.preventDefault(); return; } if (input.value.length >= 7) { e.preventDefault(); return; } } // Use inputPattern for digit validation if (!e.key.match(rules.inputPattern)) { e.preventDefault(); } }); } validateInput(input, rules, isBlur = false) { const value = input.value.trim(); let isValid = true; let message = ''; // Add validating class during check input.classList.add('is-validating'); // Required field validation if (input.required && !value) { isValid = false; message = 'This field is required'; this.updateValidationUI(input, false, message); return false; } // Special validation for accounting code if (input.dataset.validate === 'accountingCode') { if (!value.startsWith('3')) { isValid = false; message = 'Must start with 3'; } } // Uniqueness check for client_code and accounting_code on blur if (isBlur && (input.id === 'clientCode' || input.id === 'accountingCode' || input.id === 'iceCode')) { fetch(`/testapp/api/validate/${input.id}/${value}/`) .then(response => response.json()) .then(data => { if (!data.available) { isValid = false; message = `This ${input.id.replace('Code', ' code')} already exists`; this.updateValidationUI(input, false, message, true); } }) .catch(error => { console.error(`Error checking ${input.id} uniqueness:`, error); }); } // Pattern validation if (rules.pattern && !value.match(rules.pattern)) { isValid = false; message = rules.messages.pattern; } // Length validation if (rules.length && value.length !== rules.length) { isValid = false; message = rules.messages.length; } if (rules.minLength && value.length < rules.minLength) { isValid = false; message = rules.messages.minLength; } if (rules.maxLength && value.length > rules.maxLength) { isValid = false; message = rules.messages.maxLength; } // Update UI with validation result setTimeout(() => { input.classList.remove('is-validating'); this.updateValidationUI(input, isValid, message, isBlur); this.checkFormValidity(); }, 300); return isValid; } checkFormValidity() { let isValid = true; const formId = this.formId; const form = document.querySelector(`#${formId}:not(.d-none), #${formId}:not(.hide)`); if (!form) { console.debug(`Form ${formId} not found or not visible`); return true; } const inputs = form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { // Check for empty required fields if (input.required && !input.value.trim()) { isValid = false; return; } // Check for validation state if (input.classList.contains('is-invalid') || (input.required && !input.classList.contains('is-valid'))) { isValid = false; return; } }); // Update save button state const saveButton = form.querySelector('button[type="submit"]'); if (saveButton) { saveButton.disabled = !isValid; console.debug(`Form ${formId} validity: ${isValid}`); } return isValid; } updateValidationUI(input, isValid, message, isBlur) { const feedback = input.nextElementSibling; if (isValid) { input.classList.remove('is-invalid'); input.classList.add('is-valid'); if (feedback && feedback.classList.contains('invalid-feedback')) { feedback.classList.remove('show'); } } else if (isBlur || input.value.length > 0) { input.classList.remove('is-valid'); input.classList.add('is-invalid'); if (feedback) { feedback.textContent = message; feedback.classList.add('show'); } } } validateForm() { let isValid = true; const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { const validationType = input.dataset.validate; const rules = this.config[validationType]; if (!this.validateInput(input, rules, true)) { isValid = false; } }); return isValid; } } // Client Management class class ClientManagement { constructor() { console.log('Initializing ClientManagement'); this.initializeValidators(); this.bindEvents(); this.loadClients(); this.loadEntities(); } initializeValidators() { this.clientValidator = new FormValidator('clientForm', ValidationConfig); this.entityValidator = new FormValidator('entityForm', ValidationConfig); } // Event Binding bindEvents() { $('#saveClientBtn').on('click', () => this.saveClient()); $('#saveEntityBtn').on('click', () => this.saveEntity()); // Reset forms on modal close $('#clientModal').on('hidden.bs.modal', () => this.resetForm('clientForm')); $('#entityModal').on('hidden.bs.modal', () => this.resetForm('entityForm')); // Tab change handlers $('#clientTabs a[data-toggle="tab"]').on('shown.bs.tab', (e) => { if (e.target.id === 'clients-tab') { this.loadClients(); } else { this.loadEntities(); } }); } // Client Operations async loadClients() { console.log('Loading clients...'); try { const response = await fetch('/testapp/api/clients/'); const data = await response.json(); const tbody = $('#clientsTableBody'); tbody.empty(); data.clients.forEach(client => { const formattedDate = this.formatDate(client.created_at); tbody.append(` <tr class="fade-in"> <td>${client.client_code}</td> <td>${client.name}</td> <td>${formattedDate}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editClient('${client.id}', '${client.name}', '${client.client_code}')"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger me-2" onclick="window.clientManagement.deleteClient('${client.id}')"> <i class="fas fa-trash"></i> </button> <a href="/testapp/clients/${client.id}/card/" class="btn btn-sm btn-outline-info"> <i class="fas fa-chart-line me-1"></i> Sales Card </a> </td> </tr> `); console.log('Client loaded:', client, formattedDate); }); } catch (error) { console.error('Error loading clients:', error); this.showToast('Error', 'Failed to load clients'); } } async saveClient() { console.log('Saving client...'); if (!this.clientValidator.validateForm()) { console.log('Client form validation failed'); return; } const formData = { name: $('#clientName').val().trim(), client_code: $('#clientCode').val().trim() }; const id = $('#clientId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/clients/${id}/update/` : '/testapp/api/clients/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Client saved successfully:', result); $('#clientModal').modal('hide'); await this.loadClients(); this.showToast('Success', 'Client saved successfully'); } } catch (error) { console.error('Error saving client:', error); this.showToast('Error', error.message); } } editClient(id, name, client_code) { console.log('Editing client:', id); $('#clientId').val(id); $('#clientName').val(name); $('#clientCode').val(client_code); $('#clientModalTitle .title-text').text('Edit Client'); $('#clientModal').modal('show'); } async deleteClient(id) { if (!confirm('Are you sure you want to delete this client?')) { return; } try { const response = await this.sendRequest( `/testapp/api/clients/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadClients(); this.showToast('Success', 'Client deleted successfully'); } } catch (error) { console.error('Error deleting client:', error); this.showToast('Error', error.message); } } // Entity Operations async loadEntities() { console.log('Loading entities...'); try { const response = await fetch('/testapp/api/entities/'); const data = await response.json(); const tbody = $('#entitiesTableBody'); tbody.empty(); data.entities.forEach(entity => { tbody.append(` <tr class="fade-in"> <td>${entity.name}</td> <td>${entity.ice_code}</td> <td>${entity.accounting_code}</td> <td>${entity.city || '-'}</td> <td>${entity.phone_number || '-'}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editEntity('${entity.id}', ${JSON.stringify(entity)})"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger" onclick="window.clientManagement.deleteEntity('${entity.id}')"> <i class="fas fa-trash"></i> </button> </td> </tr> `); }); } catch (error) { console.error('Error loading entities:', error); this.showToast('Error', 'Failed to load entities'); } } async saveEntity() { console.log('Saving entity...'); if (!this.entityValidator.validateForm()) { console.log('Entity form validation failed'); return; } const formData = { name: $('#entityName').val().trim(), ice_code: $('#iceCode').val().trim(), accounting_code: $('#accountingCode').val().trim(), city: $('#city').val().trim(), phone_number: $('#phoneNumber').val().trim() }; const id = $('#entityId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/entities/${id}/update/` : '/testapp/api/entities/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Entity saved successfully:', result); $('#entityModal').modal('hide'); await this.loadEntities(); this.showToast('Success', 'Entity saved successfully'); } } catch (error) { console.error('Error saving entity:', error); this.showToast('Error', error.message); } } editEntity(id, entityData) { console.log('Editing entity:', id); $('#entityId').val(id); $('#entityName').val(entityData.name); $('#iceCode').val(entityData.ice_code); $('#accountingCode').val(entityData.accounting_code); $('#city').val(entityData.city || ''); $('#phoneNumber').val(entityData.phone_number || ''); $('#entityModalTitle .title-text').text('Edit Entity'); $('#entityModal').modal('show'); } async deleteEntity(id) { if (!confirm('Are you sure you want to delete this entity?')) { return; } try { const response = await this.sendRequest( `/testapp/api/entities/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadEntities(); this.showToast('Success', 'Entity deleted successfully'); } } catch (error) { console.error('Error deleting entity:', error); this.showToast('Error', error.message); } } // Utility Methods formatDate(dateString) { if (!dateString) return '-'; try { const date = new Date(dateString); return date.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); } catch (e) { console.error('Error formatting date:', e); return dateString; } } async sendRequest(url, method, data = null) { const options = { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }; if (data && method !== 'GET') { options.body = JSON.stringify(data); } const response = await fetch(url, options); if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'Request failed'); } return response; } resetForm(formId) { console.log(`Resetting form: ${formId}`); const form = document.getElementById(formId); form.reset(); const inputs = form.querySelectorAll('.form-control'); inputs.forEach(input => { input.classList.remove('is-valid', 'is-invalid', 'is-validating'); const feedback = input.nextElementSibling; if (feedback) { feedback.classList.remove('show'); } }); // Reset titles if (formId === 'clientForm') { $('#clientModalTitle .title-text').text('Add New Client'); $('#clientId').val(''); } else { $('#entityModalTitle .title-text').text('Add New Entity'); $('#entityId').val(''); } } showToast(title, message) { // You can replace this with your preferred notification library alert(`${title}: ${message}`); } } // Initialize when document is ready document.addEventListener('DOMContentLoaded', () => { console.log('Initializing client management module'); window.clientManagement = new ClientManagement(); }); </script> {% endblock %}
```

# templates/client/components/client_modal.html

```html
<!-- Client Modal --> <div class="modal fade" id="clientModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="clientModalTitle"> <i class="fas fa-user-plus me-2"></i> <span class="title-text">Add New Client</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="clientForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="clientId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="clientName" class="form-label"> <i class="fas fa-signature me-2"></i>Client Name </label> <input type="text" class="form-control" id="clientName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- Client Code Field --> <div class="form-group mb-4"> <label for="clientCode" class="form-label"> <i class="fas fa-hashtag me-2"></i>Client Code </label> <input type="text" class="form-control" id="clientCode" data-validate="clientCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Enter a unique code (5-10 digits) </small> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i>Cancel </button> <button type="button" class="btn btn-primary" id="saveClientBtn"> <i class="fas fa-save me-2"></i>Save Client </button> </div> </div> </div> </div>
```

# templates/client/components/entity_modal.html

```html
<!-- Entity Modal --> <div class="modal fade" id="entityModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="entityModalTitle"> <i class="fas fa-building me-2"></i> <span class="title-text">Add New Entity</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="entityForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="entityId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="entityName" class="form-label"> <i class="fas fa-signature me-2"></i>Entity Name </label> <input type="text" class="form-control" id="entityName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- ICE Code Field --> <div class="form-group mb-4"> <label for="iceCode" class="form-label"> <i class="fas fa-fingerprint me-2"></i>ICE Code </label> <input type="text" class="form-control" id="iceCode" data-validate="iceCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must be exactly 15 digits </small> </div> <!-- Accounting Code Field --> <div class="form-group mb-4"> <label for="accountingCode" class="form-label"> <i class="fas fa-calculator me-2"></i>Accounting Code </label> <input type="text" class="form-control" id="accountingCode" data-validate="accountingCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must start with 3 and be 5-7 digits long </small> </div> <!-- Optional Fields --> <div class="row"> <div class="col-md-6"> <div class="form-group mb-4"> <label for="city" class="form-label"> <i class="fas fa-city me-2"></i>City </label> <input type="text" class="form-control" id="city"> </div> </div> <div class="col-md-6"> <div class="form-group mb-4"> <label for="phoneNumber" class="form-label"> <i class="fas fa-phone me-2"></i>Phone Number </label> <input type="tel" class="form-control" id="phoneNumber"> </div> </div> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i>Cancel </button> <button type="button" class="btn btn-primary" id="saveEntityBtn"> <i class="fas fa-save me-2"></i>Save Entity </button> </div> </div> </div> </div>
```

# templates/client/sale_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Client Sales</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#saleModal"> <i class="fas fa-plus"></i> New Sale </button> </div> <!-- Sales Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Amount</th> <th>Notes</th> </tr> </thead> <tbody> {% for sale in sales %} <tr> <td>{{ sale.date|date:"Y-m-d" }}</td> <td>{{ sale.client.name }}</td> <td class="text-right">{{ sale.amount|floatformat:2 }}</td> <td>{{ sale.notes }}</td> </tr> {% empty %} <tr> <td colspan="4" class="text-center">No sales recorded yet</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Sale Modal --> <div class="modal fade" id="saleModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Record New Sale</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="saleForm"> {% csrf_token %} <div class="form-group"> <label for="client">Client</label> <input type="text" class="form-control" id="client" placeholder="Search client..." required> <input type="hidden" id="client_id" name="client" required> </div> <div class="form-group"> <label for="date">Date</label> <input type="date" class="form-control" id="date" name="date" value="{% now 'Y-m-d' %}" required> </div> <div class="form-group"> <label for="amount">Amount</label> <input type="number" class="form-control" id="amount" name="amount" step="0.01" min="0.01" required> </div> <div class="form-group"> <label for="notes">Notes</label> <textarea class="form-control" id="notes" name="notes" rows="2"></textarea> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveSale">Save</button> </div> </div> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 2, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Handle form submission $('#saveSale').click(function() { const form = $('#saleForm'); $.ajax({ url: "{% url 'create-sale' %}", method: 'POST', data: form.serialize(), success: function(response) { $('#saleModal').modal('hide'); showToast('Sale recorded successfully'); location.reload(); }, error: function(xhr) { showToast(xhr.responseJSON.message, 'error'); } }); }); }); </script> {% endblock %}
```

# templates/home.html

```html
{% extends 'base.html' %} {% block title %}Home - MyProject{% endblock %} {% block content %} <h1>Welcome to MyProject!</h1> <p>This is the home page.</p> {% endblock %}
```

# templates/invoice/invoice_confirm_delete.html

```html
{% extends 'base.html' %} {% block title %}Delete Invoice{% endblock %} {% block content %} <h1>Delete Invoice</h1> <p>Are you sure you want to delete the invoice with reference "{{ invoice.ref }}"?</p> <form method="post"> {% csrf_token %} <button type="submit" class="btn btn-danger">Confirm Deletion</button> <a href="{% url 'invoice-list' %}" class="btn btn-secondary">Cancel</a> </form> {% endblock %}
```

# templates/invoice/invoice_form.html

```html
{% extends 'base.html' %} {% load humanize %} {% load accounting_filters %} {% block title %}Invoice Form{% endblock %} {% block content %} <h1>{{ view.object.pk|default:'Add New Invoice' }}</h1> <form method="post"> {% csrf_token %} {{ form.as_p }} {{ products.management_form }} <div style="display: none;"> {% for product_form in products %} <div class="product-form"> {{ product_form.id }} {{ product_form.product }} {{ product_form.quantity }} {{ product_form.unit_price }} {{ product_form.reduction_rate }} {{ product_form.vat_rate }} {% if product_form.instance.pk %}{{ product_form.DELETE }}{% endif %} </div> {% endfor %} </div> <button type="submit" class="btn btn-success mt-4">Save</button> <a href="{% url 'invoice-list' %}" class="btn btn-secondary mt-4">Cancel</a> </form> <!-- Add Product Button after Invoice is saved --> {% if view.object.pk %} <button type="button" id="add-product" class="btn btn-primary mt-4" data-toggle="modal" data-target="#productModal">Add Product</button> <!-- Table to show all products linked to the current invoice --> <h3 class="mt-4">Products in Invoice</h3> <table class="table table-hover table-bordered mt-2"> <thead class="thead-dark"> <tr> <th>Product</th> <th>Fiscal Label</th> <th>Expense Code</th> <th>Quantity</th> <th>Unit Price</th> <th>Reduction Rate (%)</th> <th>VAT Rate (%)</th> <th>Subtotal</th> <th>Actions</th> </tr> </thead> <tbody id="product-list"> {% for product in view.object.products.all %} <tr data-product-id="{{ product.pk }}"> <td>{{ product.product.name }}</td> <td>{{ product.product.fiscal_label }}</td> <td>{{ product.product.expense_code }}</td> <td>{{ product.quantity }}</td> <td>{{ product.unit_price|space_thousands }}</td> <td>{{ product.reduction_rate }}</td> <td>{{ product.vat_rate }}</td> <td>{{ product.subtotal|space_thousands }}</td> <td> <button class="btn btn-warning btn-sm edit-product" data-product-id="{{ product.pk }}">Edit</button> <button class="btn btn-danger btn-sm delete-product" data-product-id="{{ product.pk }}">Delete</button> </td> </tr> {% endfor %} </tbody> <tfoot> <tr> <th colspan="7" class="text-right">Raw Total:</th> <th id="raw-total">{{ view.object.raw_amount|space_thousands }}</th> </tr> <tr> <th colspan="7" class="text-right">Total Tax Amount:</th> <th id="tax-total">{{ view.object.total_tax_amount|space_thousands }}</th> </tr> <tr> <th colspan="7" class="text-right text-primary">Total Amount (Including Tax):</th> <th id="total-amount">{{ view.object.total_amount|space_thousands }}</th> </tr> </tfoot> </table> <!-- Accounting Summary --> <h3 class="mt-4">Accounting Summary</h3> <table class="table table-hover table-bordered mt-2 accounting-table"> <thead class="thead-dark"> <tr> <th class="align-middle">Date</th> <th class="align-middle label-column">Label</th> <th class="text-right align-middle">Debit</th> <th class="text-right align-middle">Credit</th> <th class="align-middle">Account Code</th> <th class="align-middle">Reference</th> <th class="align-middle">Journal</th> <th class="align-middle">Counterpart</th> </tr> </thead> <tbody> {% for entry in view.object.get_accounting_entries %} <tr class="{% if entry.credit %}total-row font-weight-bold{% elif 'VAT' in entry.label %}vat-row{% endif %}"> <td>{{ entry.date|date:"Y-m-d" }}</td> <td>{{ entry.label }}</td> <td class="text-right"> {% if entry.debit %} {{ entry.debit|space_thousands }} {% endif %} </td> <td class="text-right"> {% if entry.credit %} {{ entry.credit|space_thousands }} {% endif %} </td> <td>{{ entry.account_code }}</td> <td>{{ entry.reference }}</td> <td class="text-center">{{ entry.journal }}</td> <td>{{ entry.counterpart }}</td> </tr> {% endfor %} </tbody> <tfoot class="bg-light"> <tr class="font-weight-bold"> <td colspan="2" class="text-right">Totals:</td> <td class="text-right"> {% with entries=view.object.get_accounting_entries %} {{ entries|sum_debit|space_thousands }} {% endwith %} </td> <td class="text-right"> {% with entries=view.object.get_accounting_entries %} {{ entries|sum_credit|space_thousands }} {% endwith %} </td> <td colspan="4"></td> </tr> </tfoot> </table> {% else %} <div class="alert alert-warning mt-4"> Save the invoice before adding products. </div> {% endif %} <!-- Modal Template for Adding Product --> <div class="modal fade" id="productModal" tabindex="-1" role="dialog" aria-labelledby="productModalLabel" aria-hidden="true"> <div class="modal-dialog" role="document"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title" id="productModalLabel">Add Product to Invoice</h5> <button type="button" class="close" data-dismiss="modal" aria-label="Close"> <span aria-hidden="true">&times;</span> </button> </div> <div class="modal-body"> <div id="modal-alert" class="alert d-none" role="alert"></div> <form id="add-product-form"> <div class="form-group"> <label for="product">Product:</label> <input type="text" id="product" name="product" class="form-control" placeholder="Search for a product..."> <input type="hidden" id="product_id" name="product_id"> <div id="new-product-fields" style="display: none;"> <input type="text" id="new-product-name" class="form-control mt-2" placeholder="New Product Name"> <input type="text" id="fiscal-label" class="form-control mt-2" placeholder="Fiscal Label"> <div class="custom-control custom-checkbox mt-2"> <input type="checkbox" class="custom-control-input" id="is-energy"> <label class="custom-control-label" for="is-energy">Is Energy Product</label> </div> </div> </div> <div class="form-group"> <label for="expense_code">Expense Code:</label> <input type="text" id="expense_code" name="expense_code" class="form-control" pattern="[0-9]{5,}" title="Expense code must be numeric and at least 5 characters long"> </div> <div class="form-group"> <label for="quantity">Quantity:</label> <input type="number" id="quantity" name="quantity" class="form-control" min="1"> <div class="invalid-feedback"> Please enter a valid quantity (minimum of 1). </div> </div> <div class="form-group"> <label for="unit_price">Unit Price:</label> <input type="number" id="unit_price" name="unit_price" class="form-control" min="0.01" step="0.01"> </div> <div class="form-group"> <label for="reduction_rate">Reduction Rate (%)</label> <input type="number" id="reduction_rate" name="reduction_rate" class="form-control" min="0" max="100" step="0.01"> </div> <div class="form-group"> <label for="vat_rate">VAT Rate (%):</label> <select id="vat_rate" name="vat_rate" class="form-control"> <option value="0.00">0%</option> <option value="7.00">7%</option> <option value="10.00">10%</option> <option value="11.00">11%</option> <option value="14.00">14%</option> <option value="16.00">16%</option> <option value="20.00">20%</option> </select> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> <button type="button" id="save-product-button" class="btn btn-primary">Save Product</button> </div> </div> </div> </div> <style> .ui-autocomplete { position: absolute; z-index: 2000; background-color: white; border: 1px solid #ccc; max-height: 200px; overflow-y: auto; list-style: none; padding: 0; margin: 0; } .ui-menu-item { padding: 8px 12px; cursor: pointer; } .ui-menu-item:hover { background-color: #f8f9fa; } </style> <script> document.addEventListener('DOMContentLoaded', function () { $('#productModal').on('hidden.bs.modal', function () { // Reset the form fields $('#add-product-form')[0].reset(); // Remove validation styles $('#add-product-form .is-invalid').removeClass('is-invalid'); // Remove error messages $('#add-product-form .invalid-feedback').remove(); }); $(document).ready(function() { $("#product").autocomplete({ minLength: 2, source: function(request, response) { $.ajax({ url: "{% url 'product-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { response(data); } }); }, select: function(event, ui) { $("#product").val(ui.item.label.split(' (')[0]); $("#product_id").val(ui.item.value); if (ui.item.value === 'new') { $('#new-product-fields').show(); $('#expense_code').val('').prop('disabled', false); } else { $('#new-product-fields').hide(); loadProductDetails(ui.item.value); } return false; } }); // Test if element exists console.log("Product input element:", $("#product").length); }); // Add this function to load product details function loadProductDetails(productId) { $.ajax({ url: `/testapp/products/${productId}/details/`, // You'll need to create this endpoint method: 'GET', success: function(data) { $('#expense_code').val(data.expense_code).prop('disabled', true); $('#vat_rate').val(data.vat_rate); }, error: function() { alert("Failed to load product details."); } }); } // Function to load products into dropdown function loadProducts(selectedProductId = null) { $.ajax({ url: "{% url 'product-autocomplete' %}", method: "GET", success: function (data) { const productSelect = document.getElementById('product'); productSelect.innerHTML = '<option value="">Select a Product</option>'; productSelect.innerHTML += '<option value="new">+ Create New Product</option>'; // Populate dropdown with products data.forEach(function (product) { const option = document.createElement('option'); option.value = product.value; option.text = product.label; productSelect.appendChild(option); }); // If a product ID is provided, select it if (selectedProductId) { $('#product').val(selectedProductId); $('#product').prop('disabled', true); $('#new-product-fields').hide(); } else { $('#product').prop('disabled', false); } }, error: function () { alert("Failed to load products."); } }); } // Modal show event handler $('#productModal').on('show.bs.modal', function () { const editingProductId = $('#save-product-button').attr('data-editing'); if (!editingProductId) { // Add mode - load all products loadProducts(); } }); // Save button click handler document.getElementById('save-product-button').addEventListener('click', function () { const productId = $('#save-product-button').attr('data-editing'); const selectedProductId = $('#product_id').val(); const quantity = $('#quantity').val(); const unitPrice = $('#unit_price').val(); const reductionRate = $('#reduction_rate').val(); const vatRate = $('#vat_rate').val(); const expenseCode = $('#expense_code').val(); const isNewProduct = selectedProductId === 'new'; // Validate fields before submission let isValid = true; let errorMessage = ""; if (!productId && !selectedProductId) { // Only validate product selection in add mode isValid = false; errorMessage += "Please select a product.\n"; } if (quantity <= 0) { isValid = false; errorMessage += "Quantity must be a positive number.\n"; } if (unitPrice <= 0) { isValid = false; errorMessage += "Unit Price must be a positive value.\n"; } if (reductionRate < 0 || reductionRate > 100) { isValid = false; errorMessage += "Reduction Rate must be between 0 and 100.\n"; } if (!/^\d{5,}$/.test(expenseCode)) { isValid = false; errorMessage += "Expense code must be numeric and at least 5 characters long.\n"; } if (isNewProduct) { if (!$('#new-product-name').val()) { isValid = false; errorMessage += "Product name is required.\n"; } if (!$('#fiscal-label').val()) { isValid = false; errorMessage += "Fiscal label is required.\n"; } } if (!isValid) { alert(errorMessage); return; } // If creating a new product if (isNewProduct && !productId) { // First create the product const productData = { name: $('#new-product-name').val(), fiscal_label: $('#fiscal-label').val(), is_energy: $('#is-energy').is(':checked'), expense_code: expenseCode, vat_rate: vatRate, csrfmiddlewaretoken: '{{ csrf_token }}' }; $.ajax({ url: "{% url 'product-ajax-create' %}", method: "POST", data: productData, success: function(response) { // Now create the invoice product with the new product ID const requestData = { quantity: quantity, unit_price: unitPrice, reduction_rate: reductionRate, vat_rate: vatRate, expense_code: expenseCode, invoice_id: '{{ view.object.pk }}', product: response.product_id, csrfmiddlewaretoken: '{{ csrf_token }}' }; $.ajax({ url: "{% url 'add-product-to-invoice' %}", method: "POST", data: requestData, success: function(response) { location.reload(); }, error: function(error) { alert("Failed to add product to invoice."); console.error(error); } }); }, error: function(error) { alert("Failed to create new product."); console.error(error); } }); } else { // Existing logic for editing or adding existing product const requestData = { quantity: quantity, unit_price: unitPrice, reduction_rate: reductionRate, vat_rate: vatRate, expense_code: expenseCode, csrfmiddlewaretoken: '{{ csrf_token }}' }; if (!productId) { // Add mode - include additional fields requestData.invoice_id = '{{ view.object.pk }}'; requestData.product = selectedProductId; } // Make AJAX request $.ajax({ url: productId ? `/testapp/invoices/edit-product/${productId}/` : "{% url 'add-product-to-invoice' %}", method: "POST", data: requestData, success: function (response) { location.reload(); }, error: function (error) { alert("Failed to save product. Please try again."); console.error(error); } }); } }); // Edit button click handler document.querySelectorAll('.edit-product').forEach(function (editButton) { editButton.addEventListener('click', function () { const productId = editButton.getAttribute('data-product-id'); // Load product data into the modal for editing $.ajax({ url: `/testapp/invoices/edit-product/${productId}/`, method: "GET", success: function (data) { // First load all products, then set the selected one loadProducts(data.product); // Populate other fields $('#product').val(data.product_name); // Add product_name to your EditProductInInvoiceView response $('#product_id').val(data.product); $('#productModalLabel').text('Edit Product in Invoice'); $('#quantity').val(data.quantity); $('#unit_price').val(data.unit_price); $('#reduction_rate').val(data.reduction_rate); $('#vat_rate').val(data.vat_rate.toFixed(2)).prop('disabled', true); $('#expense_code').val(data.expense_code).prop('disabled', true); // Set editing mode $('#save-product-button').attr('data-editing', productId); $('#productModal').modal('show'); }, error: function (error) { alert("Failed to load product data for editing."); } }); }); }); // Delete button click handler document.querySelectorAll('.delete-product').forEach(function (deleteButton) { deleteButton.addEventListener('click', function () { const productId = deleteButton.getAttribute('data-product-id'); if (confirm("Are you sure you want to delete this product?")) { $.ajax({ url: `/testapp/invoices/edit-product/${productId}/`, method: "DELETE", headers: { 'X-CSRFToken': '{{ csrf_token }}' }, success: function (response) { deleteButton.closest('tr').remove(); }, error: function (error) { alert("Failed to delete product. Please try again."); } }); } }); }); // Modal close handler $('#productModal').on('hidden.bs.modal', function () { $('#add-product-form')[0].reset(); $('#save-product-button').removeAttr('data-editing'); $('#productModalLabel').text('Add Product to Invoice'); $('#product').prop('disabled', false); // Re-enable product selection $('#new-product-fields').hide(); // Hide new product fields $('#expense_code').prop('disabled', false); // Reset expense code field }); const form = document.getElementById("add-product-form"); const alertBox = document.getElementById("modal-alert"); document.getElementById("save-product-button").addEventListener("click", () => { // Clear previous alerts alertBox.classList.add("d-none"); alertBox.innerHTML = ""; // Reset validation states const inputs = form.querySelectorAll(".form-control"); inputs.forEach((input) => { input.classList.remove("is-invalid"); }); // Validate fields let isValid = true; // Example validation: Quantity const quantity = document.getElementById("quantity"); if (!quantity.value || quantity.value < 1) { isValid = false; quantity.classList.add("is-invalid"); quantity.nextElementSibling.textContent = "Quantity must be at least 1."; } // Example validation: Expense Code const expenseCode = document.getElementById("expense_code"); if (!quantity.value ||!/^[0-9]{5,}$/.test(expenseCode.value)) { isValid = false; expenseCode.classList.add("is-invalid"); expenseCode.nextElementSibling.textContent = "Expense code must be numeric and at least 5 characters long."; } if (isValid) { // Simulate form submission success alertBox.className = "alert alert-success"; alertBox.textContent = "Product saved successfully!"; alertBox.classList.remove("d-none"); // Close modal after 2 seconds setTimeout(() => { $("#productModal").modal("hide"); }, 2000); } else { // Show error alert alertBox.className = "alert alert-danger"; alertBox.textContent = "Please fix the errors in the form."; alertBox.classList.remove("d-none"); } }); }); </script> {% endblock %}
```

# templates/invoice/invoice_list.html

```html
{% extends 'base.html' %} {% load humanize %} {% block title %}Invoice List{% endblock %} {% block content %} <script> console.log("Script block loaded"); document.addEventListener('DOMContentLoaded', function() { console.log("DOM loaded"); // Initialize supplier autocomplete $('#supplier-filter').autocomplete({ source: "{% url 'supplier-autocomplete' %}", minLength: 2, select: function(event, ui) { $(this).val(ui.item.label); $('#supplier-filter-id').val(ui.item.value); return false; } }); // Filter functionality const applyButton = document.getElementById('apply-filters'); if (applyButton) { applyButton.addEventListener('click', function(e) { e.preventDefault(); // Debug: Log all form elements const form = document.getElementById('filter-form'); console.log("All form elements:", form.elements); console.log("Apply button clicked"); // Get all form values including checkboxes and select2 const filters = {}; // Get standard form inputs const formData = new FormData(document.getElementById('filter-form')); // Debug log console.log("Form data before processing:", Object.fromEntries(formData)); // Process each form element $('#filter-form').find('input').each(function() { const input = $(this); const name = input.attr('name'); if (!name) return; // Skip if no name attribute if (input.is(':checkbox')) { // Only add checked checkboxes if (input.is(':checked')) { filters[name] = input.val(); } } else if (name === 'supplier') { // Use the hidden supplier_id field instead of the display name const supplierId = $('#supplier-filter-id').val(); if (supplierId) { filters['supplier'] = supplierId; } } else if (name === 'product') { // Use the hidden product_id field instead of the display name const productId = $('#product-filter-id').val(); if (productId) { filters['product'] = productId; } } else { // Handle regular inputs const value = input.val(); if (value) { filters[name] = value; } } }); // Debug logs console.log("Final filters object:", filters); // Apply filters const searchParams = new URLSearchParams(filters); window.location.search = searchParams.toString(); }); } else { console.error("Apply button not found"); } // Reset filters const resetButton = document.getElementById('reset-filters'); if (resetButton) { resetButton.addEventListener('click', function(e) { e.preventDefault(); console.log("Reset clicked"); // Reset form document.getElementById('filter-form').reset(); // Reset supplier filter $('#supplier-filter, #supplier-filter-id').val(''); // Uncheck all checkboxes $('input[type="checkbox"]').prop('checked', false); // Clear URL parameters and reload window.history.pushState({}, '', `${window.location.pathname}?${urlParams.toString()}`); }); } const filterPanel = document.querySelector('.filter-panel'); // Initialize filters from URL parameters const urlParams = new URLSearchParams(window.location.search); if (urlParams.toString() !== '') { filterPanel.style.display = 'block'; // Force display of the panel } for (let [key, value] of urlParams.entries()) { const input = document.querySelector(`[name="${key}"]`); if (input) { if (input.type === 'checkbox') { input.checked = value === '1'; } else { input.value = value; } } } // Debug log for URL parameters console.log("URL parameters:", Object.fromEntries(urlParams)); // Show/hide filter panel $('#toggle-filters').click(function(e) { $('.filter-panel').slideToggle(); $(this).find('i').toggleClass('fa-filter fa-filter-slash'); }); const tableRows = document.querySelectorAll('.table-hover tbody tr'); tableRows.forEach(row => { row.addEventListener('click', function () { // Remove 'active-row' from all rows tableRows.forEach(r => r.classList.remove('active-row')); // Add 'active-row' to the clicked row this.classList.add('active-row'); }); }); const rowButtons = document.querySelectorAll('td .btn'); rowButtons.forEach(button => { button.addEventListener('click', function () { const row = this.closest('tr'); row.classList.add('active-row'); setTimeout(() => { row.classList.remove('active-row'); }, 1000); // Highlight row for 1 second }); }); }); </script> <h1>Invoice List</h1> <div class="filter-section mb-4"> <a href="{% url 'invoice-create' %}" class="btn btn-primary btn-lg shadow-sm rounded-pill"> <i class="fas fa-plus-circle"></i> Add New Invoice </a> <!-- Filter Toggle Button --> <div class="d-flex justify-content-between align-items-center mb-3"> <button class="btn btn-outline-secondary shadow-sm rounded-pill" id="toggle-filters"> <i class="fas fa-filter"></i> Filters <span class="badge badge-primary ml-2 active-filters-count" style="display:none">0</span> </button> <div class="active-filters"> <span class="results-count"></span> </div> </div> <!-- Filter Panel --> <div class="filter-panel card" {% if not active_filters %}style="display:none"{% endif %}> <div class="card-body"> <form id="filter-form"> <div class="row"> <!-- Date Range Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Date Range</label> <div class="input-group"> <input type="date" class="form-control" name="date_from" id="date-from"> <div class="input-group-prepend input-group-append"> <span class="input-group-text">to</span> </div> <input type="date" class="form-control" name="date_to" id="date-to"> </div> </div> <!-- Supplier Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Supplier</label> <input type="text" class="form-control" id="supplier-filter" name="supplier" placeholder="Search supplier..."> <input type="hidden" id="supplier-filter-id" name="supplier_id"> </div> <!-- Payment Status Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Payment Status</label> <select class="form-control w-100" name="payment_status" id="payment-status"> <option value="">All</option> <option value="not_paid">Not Paid</option> <option value="partially_paid">Partially Paid</option> <option value="paid">Paid</option> </select> </div> <!-- Amount Range Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Amount Range</label> <div class="input-group"> <input type="number" class="form-control" name="amount_min" id="amount-min" placeholder="Min"> <div class="input-group-prepend input-group-append"> <span class="input-group-text">to</span> </div> <input type="number" class="form-control" name="amount_max" id="amount-max" placeholder="Max"> </div> </div> <!-- Export Status Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Export Status</label> <select class="form-control w-100" name="export_status" id="export-status"> <option value="">All</option> <option value="exported">Exported</option> <option value="not_exported">Not Exported</option> </select> </div> <!-- Document Type Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Document Type</label> <select class="form-control w-100" name="document_type" id="document-type"> <option value="">All</option> <option value="invoice">Invoice</option> <option value="credit_note">Credit Note</option> </select> </div> <!-- Product Filter --> <div class="col-md-6 col-lg-4 mb-3"> <label>Product</label> <input type="text" class="form-control" id="product-filter" name="product" placeholder="Search product..."> <input type="hidden" id="product-filter-id" name="product_id"> </div> <!-- Payment Status Checks --> <div class="col-md-6 col-lg-4 mb-3"> <label>Payment Checks</label> <div class="form-group"> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="pending-checks" name="has_pending_checks" value="1"> <label class="custom-control-label" for="pending-checks">Has Pending Checks</label> </div> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="delivered-unpaid" name="has_delivered_unpaid" value="1"> <label class="custom-control-label" for="delivered-unpaid">Delivered But Unpaid</label> </div> </div> </div> <!-- Other Filters --> <div class="col-md-6 col-lg-4 mb-3"> <label>Additional Filters</label> <div class="form-group"> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="is-energy" name="is_energy" value="1"> <label class="custom-control-label" for="is-energy">Energy Supplier</label> </div> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="is-overdue" name="is_overdue" value="1"> <label class="custom-control-label" for="is-overdue">Overdue Invoices</label> </div> </div> </div> <!-- Credit Note Status --> <div class="col-md-6 col-lg-4 mb-3"> <label>Credit Note Status</label> <select class="form-control w-100" name="credit_note_status"> <option value="">All</option> <option value="has_credit_notes">Has Credit Notes</option> <option value="no_credit_notes">No Credit Notes</option> <option value="partially_credited">Partially Credited</option> </select> </div> <!-- Due Date Range --> <div class="col-md-6 col-lg-4 mb-3"> <label>Due Date Range</label> <div class="input-group"> <input type="date" class="form-control" name="due_date_from"> <div class="input-group-prepend input-group-append"> <span class="input-group-text">to</span> </div> <input type="date" class="form-control" name="due_date_to"> </div> </div> <!-- Filter Buttons --> <div class="d-flex justify-content-end mt-3"> <button type="button" id="reset-filters" class="btn btn-outline-danger rounded-pill mr-2"> <i class="fas fa-times-circle"></i> Reset </button> <button type="button" id="apply-filters" class="btn btn-primary rounded-pill"> <i class="fas fa-check-circle"></i> Apply Filters </button> </div> </div> </form> </div> </div> </div> <div class="table-responsive" id="invoice-table-wrapper"> <table class="table mt-4 table-hover"> <thead> <tr> <th>Export</th> <th>Date</th> <th>Reference</th> <th>Supplier</th> <th>Fiscal Label</th> <th>Raw Amount</th> <th>Tax Rate (%)</th> <th>Tax Amount</th> <th>Total Amount (Incl. Tax)</th> <th>Status</th> <th>Actions</th> <th>Details</th> </tr> </thead> <tbody> {% for invoice in invoices %} {% if invoice.type == 'invoice' %} <tr class="{% if invoice.payment_status == 'paid' %}table-success{% elif invoice.exported_at %}table-light{% endif %}"> <td> {% if invoice.exported_at %} <span class="text-muted"> Exported {{ invoice.exported_at|date:"d-m-Y" }} <button type="button" class="btn btn-warning btn-sm unexport-btn ml-2" data-invoice-id="{{ invoice.id }}"> <i class="fas fa-undo"></i> </button> </span> {% else %} <input type="checkbox" name="invoice_ids" value="{{ invoice.id }}" class="export-checkbox" {% if invoice.payment_status == 'paid' %}disabled{% endif %}> {% endif %} </td> <td>{{ invoice.date }}</td> <td>{{ invoice.ref }}</td> <td>{{ invoice.supplier.name }}</td> <td>{{ invoice.fiscal_label }}</td> <td>{{ invoice.raw_amount|floatformat:2|intcomma }}</td> <td> {% with invoice.products.all|length as product_count %} {% for product in invoice.products.all %} {{ product.vat_rate }}{% if not forloop.last %}, {% endif %} {% endfor %} {% endwith %} </td> <td> {% if invoice.total_tax_amount %} {{ invoice.total_tax_amount|floatformat:2|intcomma }} {% else %} <strong>Tax Missing</strong> {% endif %} </td> <td class="text-right"> {{ invoice.total_amount|floatformat:2|intcomma }} {% if invoice.credit_notes.exists %} <br> <small class="text-muted"> Net: {{ invoice.net_amount|floatformat:2|intcomma }} </small> <button class="btn btn-link btn-sm p-0 ml-1 toggle-credit-notes" data-invoice="{{ invoice.id }}"> <i class="fas fa-receipt"></i> </button> {% endif %} </td> <td> {% if invoice.payment_status == 'paid' %} <span class="badge badge-success"> <i class="fas fa-lock"></i> Paid </span> {% else %} {% if invoice.credit_notes.exists %} <span class="badge badge-info"> Partially Credited <small>({{ invoice.credit_notes.count }} note{{ invoice.credit_notes.count|pluralize }})</small> </span> {% endif %} <span class="badge {% if invoice.payment_status == 'partially_paid' %}badge-warning{% else %}badge-danger{% endif %}"> {% if invoice.payment_status == 'partially_paid' %} Partially Paid <small>({{ invoice.payments_summary.percentage_paid|floatformat:1 }}%)</small> {% else %} Not Paid {% endif %} </span> {% endif %} </td> <td> {% if not invoice.payment_status == 'paid' %} <a href="{% url 'invoice-update' invoice.pk %}" class="btn btn-warning btn-sm rounded-pill shadow-sm {% if invoice.exported_at %}disabled{% endif %}"> <i class="fas fa-edit"></i> Edit </a> <a href="{% url 'invoice-delete' invoice.pk %}" class="btn btn-danger btn-sm rounded-pill shadow-sm {% if invoice.exported_at %}disabled{% endif %}"> <i class="fas fa-trash-alt"></i> Delete </a> <button class="btn btn-outline-info btn-sm rounded-pill shadow-sm" data-toggle="modal" data-target="#creditNoteModal" data-invoice-id="{{ invoice.id }}" {% if not invoice.can_be_credited %}disabled{% endif %}> <i class="fas fa-receipt"></i> Credit Note </button> {% else %} <button class="btn btn-secondary" disabled> <i class="fas fa-lock"></i> Paid </button> {% endif %} </td> <td> <button class="btn btn-info" data-toggle="modal" data-target="#invoiceDetailsModal" data-invoice="{{ invoice.pk }}">Details</button> <button class="btn btn-outline-success btn-sm rounded-pill shadow-sm" data-toggle="modal" data-target="#paymentDetailsModal" data-invoice="{{ invoice.pk }}"> <i class="fas fa-money-check-alt"></i> Payment Details </button> <button class="btn btn-secondary btn-sm rounded-pill shadow-sm accounting-summary-btn" data-invoice-id="{{ invoice.id }}" title="Show Accounting Summary"> <i class="fas fa-book"></i> </button> </td> </tr> </tr> {% if invoice.credit_notes.exists %} <tr class="credit-notes-row d-none bg-light" data-parent="{{ invoice.id }}"> <td colspan="12"> <div class="ml-4"> <h6 class="mb-3"> <i class="fas fa-receipt"></i> Credit Notes for Invoice {{ invoice.ref }} </h6> <table class="table table-sm"> <thead class="thead-light"> <tr> <th>Date</th> <th>Reference</th> <th>Products</th> <th class="text-right">Amount</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for credit_note in invoice.credit_notes.all %} <tr> <td>{{ credit_note.date|date:"Y-m-d" }}</td> <td>{{ credit_note.ref }}</td> <td> {% for product in credit_note.products.all %} {{ product.product.name }} ({{ product.quantity }}) {% if not forloop.last %}, {% endif %} {% endfor %} </td> <td class="text-right text-danger"> -{{ credit_note.total_amount|floatformat:2|intcomma }} </td> <td> <span class="badge badge-info"> <i class="fas fa-receipt"></i> Credit Note </span> {% if credit_note.exported_at %} <span class="badge badge-secondary"> <i class="fas fa-file-export"></i> Exported </span> {% endif %} </td> <td> <button class="btn btn-outline-primary btn-sm rounded-pill shadow-sm" data-toggle="modal" data-target="#invoiceDetailsModal" data-invoice="{{ credit_note.id }}"> <i class="fas fa-info-circle"></i> Details </button> </td> </tr> {% endfor %} <tr class="font-weight-bold"> <td colspan="3" class="text-right">Net Balance:</td> <td class="text-right">{{ invoice.net_amount|floatformat:2|intcomma }}</td> <td colspan="2"></td> </tr> </tbody> </table> </div> </td> </tr> {% endif %} {% endif %} {% endfor %} </tbody> </table> </div> <!-- Export Button --> <div class="d-flex justify-content-end mt-3"> <button type="button" id="export-selected" class="btn btn-success btn-lg rounded-pill shadow" disabled> <i class="fas fa-file-export"></i> Export Selected </button> </div> <!-- Modal Template for Invoice Details --> <div class="modal fade" id="invoiceDetailsModal" tabindex="-1" role="dialog" aria-labelledby="invoiceDetailsModalLabel"> <div class="modal-dialog modal-lg" role="document"> <!-- Added modal-lg for larger modal --> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title" id="invoiceDetailsModalLabel"> <i class="fas fa-info-circle"></i>Invoice Details </h5> <button type="button" class="close" data-dismiss="modal" aria-label="Close"> <span aria-hidden="true">&times;</span> </button> </div> <div class="modal-body modal-scrollable-content"> <table class="table table-striped"> <thead> <tr> <th>Product</th> <th>Unit Price</th> <th>Quantity</th> <th>VAT Rate</th> <th>Reduction Rate</th> <th>Raw Price</th> </tr> </thead> <tbody id="invoice-details-table"> <!-- Filled by JavaScript --> </tbody> </table> <div id="vat-summary"></div> <div id="total-amount-summary"></div> </div> <div class="modal-footer"> <button type="button" class="btn btn-primary btn-sm" data-dismiss="modal"> <i class="fas fa-check"></i> Done </button> </div> </div> </div> </div> <!-- Payment Details Modal --> <div class="modal fade" id="paymentDetailsModal"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <i class="fas fa-money-bill"></i> Payment Details <small id="invoice-ref" class="text-muted"></small> </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-3"> <div class="card shadow-sm"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Amount Due</h6> <h4 id="amount-due" class="card-title mb-0 text-primary"></h4> </div> </div> </div> <div class="col-md-3"> <div class="card shadow-sm"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Amount Paid</h6> <h4 id="amount-paid" class="card-title mb-0 text-success"></h4> </div> </div> </div> <div class="col-md-3"> <div class="card shadow-sm"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Amount to Issue</h6> <h4 id="amount-to-issue" class="card-title mb-0 text-info"></h4> </div> </div> </div> <div class="col-md-3"> <div class="card shadow-sm"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Remaining</h6> <h4 id="remaining-amount" class="card-title mb-0 text-warning"></h4> </div> </div> </div> </div> <!-- Progress Bar --> <div class="progress mb-4" style="height: 25px;"> <div id="payment-progress" class="progress-bar" role="progressbar" style="width: 0%"></div> </div> <!-- Detailed Breakdown --> <div class="row mb-4"> <div class="col-md-6"> <div class="d-flex justify-content-between align-items-center mb-2"> <span>Pending Payments:</span> <h5 id="pending-amount" class="mb-0"></h5> </div> <div class="d-flex justify-content-between align-items-center"> <span>Delivered Payments:</span> <h5 id="delivered-amount" class="mb-0"></h5> </div> </div> </div> <!-- Checks Table --> <div class="table-responsive"> <table class="table table-hover"> <thead class="thead-light"> <tr> <th>Reference</th> <th>Amount</th> <th>Created</th> <th>Delivered</th> <th>Paid</th> <th>Status</th> </tr> </thead> <tbody id="payment-checks-tbody"></tbody> </table> </div> </div> </div> </div> </div> <!-- Credit Note Modal --> <div class="modal fade" id="creditNoteModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <i class="fas fa-receipt"></i> Create Credit Note </h5> <button type="button" class="close text-white" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Credit Note Info --> <div class="row mb-4"> <div class="col-md-6"> <label for="credit-note-ref">Credit Note Reference *</label> <input type="text" id="credit-note-ref" class="form-control" required> </div> <div class="col-md-6"> <label for="credit-note-date">Date *</label> <input type="date" id="credit-note-date" class="form-control" required> </div> </div> <!-- Original Invoice Info --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <h6>Original Invoice</h6> <div id="original-invoice-details"></div> </div> <div class="col-md-6"> <h6>Net Balance After Credit</h6> <div id="net-balance-details"></div> </div> </div> </div> </div> <!-- Products Selection --> <form id="credit-note-form"> <input type="hidden" id="original-invoice-id"> <table class="table" id="products-table"> <thead> <tr> <th>Product</th> <th>Original Qty</th> <th>Already Credited</th> <th>Available</th> <th>Credit Qty</th> <th>Unit Price</th> <th>Subtotal</th> </tr> </thead> <tbody></tbody> <tfoot> <tr> <th colspan="6" class="text-right">Total Credit Amount:</th> <th class="text-right" id="total-credit-amount">0.00</th> </tr> </tfoot> </table> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary btn-sm" data-dismiss="modal"> <i class="fas fa-times"></i> Cancel </button> <button type="button" class="btn btn-info btn-sm" id="save-credit-note"> <i class="fas fa-save"></i> Create Credit Note </button> </div> </div> </div> </div> <!-- Accounting Summary Modal --> <div class="modal fade" id="accountingSummaryModal" tabindex="-1"> <div class="modal-dialog modal-xl"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <i class="fas fa-book"></i> Accounting Summary </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="accordion" id="accountingEntries"> <!-- Original Invoice Section --> <div class="card"> <div class="card-header bg-primary text-white"> <h6 class="mb-0">Original Invoice Entries</h6> </div> <div class="card-body p-0"> <table class="table table-striped mb-0"> <thead> <tr> <th>Date</th> <th>Account</th> <th>Label</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th>Reference</th> <th>Journal</th> </tr> </thead> <tbody id="originalEntries"></tbody> </table> </div> </div> <!-- Credit Notes Section (shown only if exists) --> <div id="creditNotesSection" class="card mt-3 d-none"> <div class="card-header bg-info text-white"> <h6 class="mb-0">Credit Note Entries</h6> </div> <div class="card-body p-0"> <table class="table table-striped mb-0"> <thead> <tr> <th>Date</th> <th>Account</th> <th>Label</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th>Reference</th> <th>Journal</th> </tr> </thead> <tbody id="creditNoteEntries"></tbody> </table> </div> </div> <!-- Net Effect Section --> <div class="card mt-3"> <div class="card-header bg-success text-white"> <h6 class="mb-0">Net Effect</h6> </div> <div class="card-body"> <div class="row"> <div class="col-md-4"> <h6>Original Amount</h6> <p id="originalTotal" class="h4"></p> </div> <div class="col-md-4"> <h6>Credit Notes</h6> <p id="creditTotal" class="h4 text-danger"></p> </div> <div class="col-md-4"> <h6>Net Amount</h6> <p id="netTotal" class="h4 font-weight-bold"></p> </div> </div> </div> </div> </div> </div> </div> </div> </div> <!-- JavaScript time!!! --> <script> // 1. Utility Functions - These are used throughout the code const Utils = { formatMoney: function(amount) { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'MAD', minimumFractionDigits: 2 }).format(amount); }, formatStatus: function(status) { return status.charAt(0).toUpperCase() + status.slice(1); } }; // 2. Modal Handlers - All modal-related functions const ModalHandlers = { // Invoice Details Modal loadInvoiceDetails: function(invoiceId) { $.ajax({ url: "{% url 'invoice-details' %}", data: { 'invoice_id': invoiceId }, success: function(data) { $('#invoice-details-table').empty(); data.products.forEach(product => { $('#invoice-details-table').append(` <tr> <td>${product.name}</td> <td>${product.unit_price}</td> <td>${product.quantity}</td> <td>${product.vat_rate}</td> <td>${product.reduction_rate}</td> <td>${product.raw_price}</td> </tr> `); }); $('#vat-summary').empty(); data.vat_subtotals.forEach(vatSubtotal => { $('#vat-summary').append( `<p><strong>Subtotal for VAT ${vatSubtotal.vat_rate}:</strong> ${vatSubtotal.subtotal}</p>` ); }); $('#total-amount-summary').html(` <strong>Total Raw Amount:</strong> ${data.total_raw_amount}<br> <strong>Total VAT Amount:</strong> ${data.total_vat}<br> <strong>Total Amount (Including Tax):</strong> ${data.total_amount} `); } }); }, getProgressBarClass: function(percentage) { if (percentage >= 100) return 'bg-success'; if (percentage > 50) return 'bg-warning'; return 'bg-danger'; }, getStatusBadge: function(status) { const badges = { 'pending': ['secondary', 'clock'], 'delivered': ['warning', 'truck'], 'paid': ['success', 'check-circle'], 'rejected': ['danger', 'times-circle'], 'cancelled': ['dark', 'ban'] }; const [color, icon] = badges[status] || ['secondary', 'question-circle']; return ` <span class="badge badge-${color}"> <i class="fas fa-${icon} mr-1"></i> ${status.charAt(0).toUpperCase() + status.slice(1)} </span> `; }, // Inside your existing ModalHandlers object loadPaymentDetails: function(invoiceId) { $.get(`/testapp/invoices/${invoiceId}/payment-details/`, function(data) { const details = data.payment_details; // Update summary cards with animations const updateAmount = (elementId, amount) => { const element = $(`#${elementId}`); element.fadeOut(200, function() { $(this).text(Utils.formatMoney(amount)).fadeIn(200); }); }; updateAmount('amount-due', details.total_amount); updateAmount('amount-paid', details.paid_amount); updateAmount('amount-to-issue', details.amount_to_issue); updateAmount('pending-amount', details.pending_amount); updateAmount('delivered-amount', details.delivered_amount); updateAmount('remaining-amount', details.remaining_to_pay); // Update progress bar const progressBar = $('#payment-progress'); progressBar .css('width', '0%') .removeClass('bg-success bg-warning bg-danger') .addClass(ModalHandlers.getProgressBarClass(details.payment_percentage)) .animate( { width: `${details.payment_percentage}%` }, 800, function() { $(this).text(`${details.payment_percentage.toFixed(1)}%`); } ); ModalHandlers.updateChecksTable(data.checks); $('#paymentDetailsModal').modal('show'); }); }, updateChecksTable: function(checks) { const tbody = $('#payment-checks-tbody'); tbody.empty(); if (checks.length === 0) { tbody.append(` <tr> <td colspan="6" class="text-center text-muted py-4"> <i class="fas fa-info-circle"></i> No checks issued yet </td> </tr> `); return; } checks.forEach(check => { tbody.append(` <tr> <td> <i class="fas fa-money-check-alt text-muted mr-2"></i> ${check.reference} </td> <td class="text-right font-weight-bold"> ${Utils.formatMoney(check.amount)} </td> <td>${check.created_at}</td> <td>${check.delivered_at || '-'}</td> <td>${check.paid_at || '-'}</td> <td> ${ModalHandlers.getStatusBadge(check.status)} </td> </tr> `); }); }, showAccountingSummary: function(invoiceId) { $.ajax({ url: `/testapp/invoices/${invoiceId}/accounting-summary/`, method: 'GET', success: function(data) { // Populate the modal $('#originalEntries').empty(); data.original_entries.forEach(entry => { $('#originalEntries').append(ModalHandlers.createAccountingRow(entry)); }); if (data.credit_note_entries.length > 0) { $('#creditNotesSection').removeClass('d-none'); $('#creditNoteEntries').empty(); data.credit_note_entries.forEach(entry => { $('#creditNoteEntries').append(ModalHandlers.createAccountingRow(entry)); }); } else { $('#creditNotesSection').addClass('d-none'); } $('#originalTotal').text(Utils.formatMoney(data.totals.original)); $('#creditTotal').text(Utils.formatMoney(data.totals.credit_notes)); $('#netTotal').text(Utils.formatMoney(data.totals.net)); $('#accountingSummaryModal').modal('show'); }, error: function(xhr) { alert('Failed to load accounting summary: ' + xhr.responseText); } }); }, createAccountingRow: function(entry) { return ` <tr> <td>${entry.date}</td> <td>${entry.account_code}</td> <td>${entry.label}</td> <td class="text-right">${entry.debit ? Utils.formatMoney(entry.debit) : ''}</td> <td class="text-right">${entry.credit ? Utils.formatMoney(entry.credit) : ''}</td> <td>${entry.reference}</td> <td>${entry.journal}</td> </tr> `; } }; // 3. Credit Note Handlers const CreditNoteHandlers = { // Store the initial net amount for calculations initialNetAmount: 0, initializeQuantityHandlers: function() { $('.credit-quantity').on('input', function() { const quantity = parseFloat($(this).val()) || 0; const available = parseFloat($(this).data('available')); if (quantity > available) { $(this).val(available); return; } CreditNoteHandlers.updateSubtotalsAndTotal(); }); }, updateNetBalance: function(creditAmount) { $('#net-balance-details').html(` <p><strong>Original Amount:</strong> ${Utils.formatMoney(this.initialNetAmount)}</p> <p><strong>Credit Amount:</strong> ${Utils.formatMoney(creditAmount)}</p> <p class="font-weight-bold">Net Balance: ${Utils.formatMoney(this.initialNetAmount - creditAmount)}</p> `); }, updateSubtotalsAndTotal: function() { let total = 0; $('.credit-quantity').each(function() { const quantity = parseFloat($(this).val()) || 0; const unitPrice = parseFloat($(this).data('unit-price')); const subtotal = quantity * unitPrice; $(this).closest('tr').find('.subtotal').text(Utils.formatMoney(subtotal)); total += subtotal; }); $('#total-credit-amount').text(Utils.formatMoney(total)); this.updateNetBalance(total); }, saveCreditNote: function() { if (!$('#credit-note-ref').val()) { alert('Please enter a credit note reference'); return; } const products = []; $('.credit-quantity').each(function() { const quantity = parseFloat($(this).val()) || 0; if (quantity > 0) { products.push({ product_id: $(this).data('product-id'), quantity: quantity }); } }); if (products.length === 0) { alert('Please select at least one product to credit'); return; } $.ajax({ url: '/testapp/invoices/create-credit-note/', method: 'POST', data: JSON.stringify({ original_invoice_id: $('#original-invoice-id').val(), ref: $('#credit-note-ref').val(), date: $('#credit-note-date').val(), products: products }), contentType: 'application/json', success: function(response) { location.reload(); }, error: function(xhr) { alert('Error creating credit note: ' + xhr.responseText); } }); } }; // 4. Filter Handlers const FilterHandlers = { updateActiveFilters: function() { const activeFilters = []; const filterLabels = { date_from: 'From', date_to: 'To', supplier: 'Supplier', payment_status: 'Payment Status', amount_min: 'Min Amount', amount_max: 'Max Amount', export_status: 'Export Status', document_type: 'Document Type' }; // Build URL parameters const urlParams = new URLSearchParams(); $('#filter-form').serializeArray().forEach(function(item) { if (item.value) { urlParams.append(item.name, item.value); activeFilters.push({ name: filterLabels[item.name], value: item.value, param: item.name }); } }); // Update filter count badge const filterCount = activeFilters.length; const countBadge = $('.active-filters-count'); if (filterCount > 0) { countBadge.text(filterCount).show(); } else { countBadge.hide(); } // Update filter tags const tagsHtml = activeFilters.map(filter => ` <span class="badge badge-info mr-2"> ${filter.name}: ${filter.value} <button type="button" class="close ml-1" data-param="${filter.param}" aria-label="Remove filter"> <span aria-hidden="true">&times;</span> </button> </span> `).join(''); $('.active-filters-tags').html(tagsHtml); }, applyFilters: function() { const filters = {}; const formData = $('#filter-form').serializeArray(); console.log("Form data being submitted:", formData); // Debug log $('#filter-form').serializeArray().forEach(function(item) { if (item.value) { filters[item.name] = item.value; } }); console.log("Final filters object:", filters); // Debug log window.location.search = new URLSearchParams(filters).toString(); }, resetFilters: function() { $('#filter-form')[0].reset(); $('#supplier-filter, #supplier-filter-id').val(''); window.location.search = ''; } }; document.addEventListener('DOMContentLoaded', function () { // Initialize Modal Events // Accounting summary button handler $(document).on('click', '.accounting-summary-btn', function() { const invoiceId = $(this).data('invoice-id'); if (!invoiceId) { alert('Invoice ID is missing.'); return; } ModalHandlers.showAccountingSummary(invoiceId); }); // Credit note toggle handler $('.toggle-credit-notes').on('click', function(e) { e.preventDefault(); e.stopPropagation(); const invoiceId = $(this).data('invoice'); const icon = $(this).find('i'); const creditNotesRow = $(`.credit-notes-row[data-parent="${invoiceId}"]`); creditNotesRow.toggleClass('d-none'); icon.toggleClass('fa-receipt fa-times-circle'); }); // Make sure toggle works for dynamically loaded content $(document).on('click', '.toggle-credit-notes', function(e) { e.preventDefault(); e.stopPropagation(); const invoiceId = $(this).data('invoice'); const icon = $(this).find('i'); const creditNotesRow = $(`.credit-notes-row[data-parent="${invoiceId}"]`); creditNotesRow.toggleClass('d-none'); icon.toggleClass('fa-receipt fa-times-circle'); }); $('#invoiceDetailsModal').on('show.bs.modal', function(event) { const invoiceId = $(event.relatedTarget).data('invoice'); ModalHandlers.loadInvoiceDetails(invoiceId); }); $('#paymentDetailsModal').on('show.bs.modal', function(event) { const invoiceId = $(event.relatedTarget).data('invoice'); ModalHandlers.loadPaymentDetails(invoiceId); }); // Initialize Credit Note Events $('#creditNoteModal').on('show.bs.modal', function(event) { const invoiceId = $(event.relatedTarget).data('invoice-id'); if (!invoiceId) { console.error('No Invoice ID found!'); return; } $('#original-invoice-id').val(invoiceId); $('#credit-note-date').val(new Date().toISOString().split('T')[0]); $.ajax({ url: `/testapp/invoices/${invoiceId}/credit-note-details/`, method: 'GET', success: function(data) { // Store initial net amount CreditNoteHandlers.initialNetAmount = data.invoice.total_amount - data.invoice.credited_amount; // Update UI $('#original-invoice-details').html(` <p><strong>Reference:</strong> ${data.invoice.ref}</p> <p><strong>Date:</strong> ${data.invoice.date}</p> <p data-amount="${data.invoice.total_amount}"> <strong>Total Amount:</strong> ${Utils.formatMoney(data.invoice.total_amount)} </p> <p><strong>Already Credited:</strong> ${Utils.formatMoney(data.invoice.credited_amount)}</p> `); CreditNoteHandlers.updateNetBalance(0); // Populate products table const tbody = $('#products-table tbody').empty(); data.products.forEach(product => { tbody.append(` <tr> <td>${product.name}</td> <td class="text-right">${product.original_quantity}</td> <td class="text-right">${product.credited_quantity}</td> <td class="text-right">${product.available_quantity}</td> <td> <input type="number" class="form-control form-control-sm credit-quantity" data-product-id="${product.id}" data-unit-price="${product.unit_price}" data-available="${product.available_quantity}" min="0" max="${product.available_quantity}" value="0"> </td> <td class="text-right">${Utils.formatMoney(product.unit_price)}</td> <td class="text-right subtotal">0.00</td> </tr> `); }); CreditNoteHandlers.initializeQuantityHandlers(); } }); }); $('#save-credit-note').on('click', function() { console.log("Save button clicked"); // Debug log CreditNoteHandlers.saveCreditNote(); }); // Export functionality const checkboxes = document.querySelectorAll('.export-checkbox'); const exportButton = document.getElementById('export-selected'); checkboxes.forEach(function(checkbox) { checkbox.addEventListener('click', function() { const checkedBoxes = document.querySelectorAll('.export-checkbox:checked'); exportButton.disabled = checkedBoxes.length === 0; console.log('Checked boxes:', checkedBoxes.length); }); }); exportButton.addEventListener('click', function() { const selectedIds = [...checkboxes] .filter(cb => cb.checked) .map(cb => cb.value); if (selectedIds.length === 0) return; fetch('{% url "export-invoices" %}', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' // Add CSRF token }, body: JSON.stringify({invoice_ids: selectedIds}) }) .then(response => { if (response.ok) return response.blob(); throw new Error('Export failed'); }) .then(blob => { const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `accounting_export_${new Date().toISOString().slice(0,19).replace(/[:-]/g, '')}.xlsx`; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); location.reload(); }) .catch(error => { alert('Failed to export invoices: ' + error.message); }); }); // Unexport functionality const unexportButtons = document.querySelectorAll('.unexport-btn'); unexportButtons.forEach(button => { button.addEventListener('click', function() { const invoiceId = this.dataset.invoiceId; if (!confirm('Are you sure you want to unexport this invoice?')) return; fetch(`/testapp/invoices/${invoiceId}/unexport/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' // Add CSRF token } }) .then(response => { if (!response.ok) throw new Error('Unexport failed'); location.reload(); }) .catch(error => { alert('Failed to unexport invoice: ' + error.message); }); }); }); // Initialize Filter Events const InvoiceFilters = { init() { $('#apply-filters').on('click', (e) => { e.preventDefault(); this.applyFilters(); }); $('#reset-filters').on('click', (e) => { e.preventDefault(); this.resetFilters(); }); this.initAutocomplete(); this.initializeFromURL(); }, async applyFilters() { const formData = new FormData($('#filter-form')[0]); const queryString = new URLSearchParams(formData).toString(); try { const response = await fetch(`${window.location.pathname}?${queryString}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }); const data = await response.json(); $('#invoice-table-wrapper').html(data.html); history.pushState({}, '', `?${queryString}`); this.updateActiveFilters(); } catch (error) { console.error('Error:', error); } }, resetFilters() { $('#filter-form')[0].reset(); $('#supplier-filter, #supplier-filter-id').val(''); history.pushState({}, '', window.location.pathname); this.applyFilters(); }, initAutocomplete() { // Initialize supplier autocomplete $('#supplier-filter').autocomplete({ source: "{% url 'supplier-autocomplete' %}", minLength: 2, select: function(event, ui) { $(this).val(ui.item.label); $('#supplier-filter-id').val(ui.item.value); return false; } }); // Initialize product filter $('#product-filter').autocomplete({ source: "{% url 'product-autocomplete' %}", minLength: 2, select: function(event, ui) { $(this).val(ui.item.label); $('#product-filter-id').val(ui.item.value); return false; } }); }, initializeFromURL() { // Initialize supplier filter const supplierValue = new URLSearchParams(window.location.search).get('supplier'); if (supplierValue) { fetch(`{% url 'supplier-autocomplete' %}?id=${supplierValue}`) .then(response => response.json()) .then(data => { if (data && data.length > 0) { const selectedOption = data[0]; $('#supplier-filter').val(selectedOption.label); $('#supplier-filter-id').val(selectedOption.value); } }) .catch(error => console.error('Failed to restore supplier:', error)); } // Initialize product filter const productValue = new URLSearchParams(window.location.search).get('product'); if (productValue) { fetch(`{% url 'product-autocomplete' %}?id=${productValue}`) .then(response => response.json()) .then(data => { if (data && data.length > 0) { const selectedOption = data[0]; $('#product-filter').val(selectedOption.label); $('#product-filter-id').val(selectedOption.value); } }) .catch(error => console.error('Failed to restore product:', error)); } }, updateActiveFilters() { const activeCount = $('#filter-form').serializeArray().filter(item => item.value).length; const badge = $('.active-filters-count'); activeCount > 0 ? badge.show().text(activeCount) : badge.hide(); } }; // Initialize filters InvoiceFilters.init(); // Initialize autocomplete for existing forms document.querySelectorAll('.product-form').forEach(addAutocomplete); }); </script> {% endblock %}
```

# templates/invoice/partials/invoice_table.html

```html
<!-- templates/invoice/partials/invoice_table.html --> <table class="table mt-4 table-hover"> <thead> <tr> <th>Export</th> <th>Date</th> <th>Reference</th> <th>Supplier</th> <th>Fiscal Label</th> <th>Raw Amount</th> <th>Tax Rate (%)</th> <th>Tax Amount</th> <th>Total Amount (Incl. Tax)</th> <th>Status</th> <th>Actions</th> <th>Details</th> </tr> </thead> <tbody> {% for invoice in invoices %} <!-- Your existing invoice row template here --> {% empty %} <tr> <td colspan="12" class="text-center"> <div class="p-4"> <i class="fas fa-search fa-2x text-muted mb-3"></i> <p class="mb-0">No invoices found matching your filters</p> <button class="btn btn-link" id="reset-filters">Clear all filters</button> </div> </td> </tr> {% endfor %} </tbody> </table>
```

# templates/login.html

```html
{% extends 'base.html' %} {% block title %}Login - MyProject{% endblock %} {% block content %} <div class="container"> <h2>Login</h2> <form method="post"> {% csrf_token %} <div class="form-group"> <label for="username">Username:</label> <input type="text" id="username" name="username" class="form-control" required> </div> <div class="form-group"> <label for="password">Password:</label> <input type="password" id="password" name="password" class="form-control" required> </div> <button type="submit" class="btn btn-primary">Login</button> </form> </div> {% endblock %}
```

# templates/presentation/presentation_list.html

```html

```

# templates/product/product_confirm_delete.html

```html
{% extends 'base.html' %} {% block title %}Delete Product{% endblock %} {% block content %} <h1>Delete Product</h1> <p>Are you sure you want to delete "{{ product.name }}"?</p> <form method="post"> {% csrf_token %} <button type="submit" class="btn btn-danger">Confirm Deletion</button> <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a> </form> {% endblock %}
```

# templates/product/product_form.html

```html
{% extends 'base.html' %} {% block title %}Product Form{% endblock %} {% block content %} <h1>{{ view.object.name|default:'Add New Product' }}</h1> <form method="post"> {% csrf_token %} {% for field in form %} {% if field.name == 'vat_rate' %} <div class="form-group"> <label>{{ field.label }}</label> <select name="{{ field.name }}" class="form-control auto-size-select"> {% for choice in field.field.choices %} <option value="{{ choice.0 }}" {% if field.value|floatformat:2 == choice.0|floatformat:2 %}selected{% endif %}> {{ choice.1 }} </option> {% endfor %} </select> </div> {% else %} <div class="form-group"> {{ field.label_tag }} {{ field }} </div> {% endif %} {% endfor %} <button type="submit" class="btn btn-success">Save</button> <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a> </form> <style> .auto-size-select { display: inline-block; min-width: 100px; /* Set a reasonable minimum width */ max-width: 100%; /* Ensure it doesn't exceed the container width */ width: auto; /* Automatically adjust to content */ } </style> <script> document.querySelectorAll('.auto-size-select').forEach(select => { select.style.width = `${select.scrollWidth}px`; }); </script> {% endblock %}
```

# templates/product/product_list.html

```html
{% extends 'base.html' %} {% block title %}Product List{% endblock %} {% block content %} <h1>Product List</h1> <a href="{% url 'product-create' %}" class="btn btn-primary">Add New Product</a> <table class="table mt-4"> <thead> <tr> <th>Name</th> <th>VAT Rate</th> <th>Expense Code</th> <th>Actions</th> </tr> </thead> <tbody> {% for product in products %} <tr> <td>{{ product.name }}</td> <td>{{ product.vat_rate }}</td> <td>{{ product.expense_code }}</td> <td> <a href="{% url 'product-update' product.pk %}" class="btn btn-warning">Edit</a> <a href="{% url 'product-delete' product.pk %}" class="btn btn-danger">Delete</a> </td> </tr> {% empty %} <tr> <td colspan="4">No products found.</td> </tr> {% endfor %} </tbody> </table> {% endblock %}
```

# templates/profile.html

```html
{% extends 'base.html' %} {% block title %}Profile{% endblock %} {% block content %} <h1>Profile Page</h1> <p>First Name: {{ user.first_name }}</p> <p>Last Name: {{ user.last_name }}</p> <p>Email: {{ user.email }}</p> {% endblock %}
```

# templates/receipt/receipt_form_modal.html

```html
<!-- Modal Header --> <div class="modal-header"> <h5 class="modal-title"> {% if receipt_type == 'check' %} <i class="fas fa-money-check"></i> {% elif receipt_type == 'lcn' %} <i class="fas fa-file-invoice-dollar"></i> {% elif receipt_type == 'cash' %} <i class="fas fa-money-bill"></i> {% else %} <i class="fas fa-exchange-alt"></i> {% endif %} {{ title }} </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <!-- Modal Body --> <div class="modal-body"> <form id="receiptForm" method="post" action="{% if receipt %}{% url 'receipt-edit' receipt_type receipt.id %}{% else %}{% url 'receipt-create' receipt_type %}{% endif %}"> {% csrf_token %} <!-- Common Fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="client">Client</label> <input type="text" class="form-control" id="client" name="client_display" placeholder="Search for a client..." required value="{% if receipt %}{{ receipt.client.name }}{% endif %}"> <input type="hidden" id="client_id" name="client" value="{% if receipt %}{{ receipt.client.id }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="entity">Entity</label> <input type="text" class="form-control" id="entity" name="entity_display" placeholder="Search for an entity..." required value="{% if receipt %}{{ receipt.entity.name }}{% endif %}"> <input type="hidden" id="entity_id" name="entity" value="{% if receipt %}{{ receipt.entity.id }}{% endif %}" required> </div> </div> </div> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label for="operation_date">Operation Date</label> <input type="date" class="form-control" id="operation_date" name="operation_date" value="{% if receipt %}{{ receipt.operation_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label for="client_year">Year</label> <select class="form-control" id="client_year" name="client_year" required> {% for year in year_choices %} <option value="{{ year }}" {% if receipt and receipt.client_year == year or year == current_year %}selected{% endif %}>{{ year }}</option> {% endfor %} </select> </div> </div> <div class="col-md-4"> <div class="form-group"> <label for="client_month">Month</label> <select class="form-control" id="client_month" name="client_month" required> {% for month in month_choices %} <option value="{{ month.0 }}" {% if receipt and receipt.client_month == month.0 or month.0 == current_month %}selected{% endif %}>{{ month.1 }}</option> {% endfor %} </select> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="amount">Amount</label> <input type="number" class="form-control" id="amount" name="amount" value="{% if receipt %}{{ receipt.amount }}{% endif %}" step="0.01" min="0.01" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="bank_account">Bank Account</label> <select class="form-control" id="bank_account" name="bank_account" required> {% for account in bank_accounts %} <option value="{{ account.id }}" {% if receipt and receipt.bank_account.id == account.id %}selected{% endif %}> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> </div> </div> {% if receipt_type == 'check' %} <!-- Check-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="check_number">Check Number</label> <input type="text" class="form-control" id="check_number" name="check_number" value="{% if receipt %}{{ receipt.check_number }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="due_date">Due Date</label> <input type="date" class="form-control" id="due_date" name="due_date" value="{% if receipt %}{{ receipt.due_date|date:'Y-m-d' }}{% endif %}" required> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="bank_name">Bank Name</label> <input type="text" class="form-control" id="bank_name" name="bank_name" value="{% if receipt %}{{ receipt.bank_name }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="branch">Branch</label> <input type="text" class="form-control" id="branch" name="branch" value="{% if receipt %}{{ receipt.branch }}{% endif %}"> </div> </div> </div> {% endif %} {% if receipt_type == 'lcn' %} <!-- LCN-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="lcn_number">LCN Number</label> <input type="text" class="form-control" id="lcn_number" name="lcn_number" value="{% if receipt %}{{ receipt.lcn_number }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="due_date">Due Date</label> <input type="date" class="form-control" id="due_date" name="due_date" value="{% if receipt %}{{ receipt.due_date|date:'Y-m-d' }}{% endif %}" required> </div> </div> </div> <div class="row"> <div class="col-md-12"> <div class="form-group"> <label for="issuing_bank">Issuing Bank</label> <input type="text" class="form-control" id="issuing_bank" name="issuing_bank" value="{% if receipt %}{{ receipt.issuing_bank }}{% endif %}" required> </div> </div> </div> {% endif %} {% if receipt_type == 'cash' or receipt_type == 'transfer' %} <!-- Cash/Transfer-specific fields --> <div class="row"> <div class="col-md-12"> <div class="form-group"> <label for="credited_account">Credited Account</label> <select class="form-control" id="credited_account" name="credited_account" required> {% for account in bank_accounts %} <option value="{{ account.id }}" {% if receipt and receipt.credited_account.id == account.id %}selected{% endif %}> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> </div> </div> {% endif %} {% if receipt_type == 'transfer' %} <!-- Transfer-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="transfer_reference">Transfer Reference</label> <input type="text" class="form-control" id="transfer_reference" name="transfer_reference" value="{% if receipt %}{{ receipt.transfer_reference }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="transfer_date">Transfer Date</label> <input type="date" class="form-control" id="transfer_date" name="transfer_date" value="{% if receipt %}{{ receipt.transfer_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}" required> </div> </div> </div> {% endif %} <div class="form-group"> <label for="notes">Notes</label> <textarea class="form-control" id="notes" name="notes" rows="2">{% if receipt %}{{ receipt.notes }}{% endif %}</textarea> </div> </form> </div> <!-- Modal Footer --> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="submit" class="btn btn-primary" form="receiptForm">Save Receipt</button> </div> <!-- Initialize autocomplete --> <script> $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 2, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 2, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Add some basic styling to autocomplete dropdown $(".ui-autocomplete").addClass("dropdown-menu").css({ 'max-height': '200px', 'overflow-y': 'auto', 'overflow-x': 'hidden', 'z-index': '9999' }); }); </script>
```

# templates/receipt/receipt_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid px-4"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-receipt text-primary me-2"></i>Receipts Management </h2> <div class="btn-group"> <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"> <i class="fas fa-plus-circle"></i> New Receipt </button> <div class="dropdown-menu"> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="check"> <i class="fas fa-money-check"></i> Check </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="lcn"> <i class="fas fa-file-invoice-dollar"></i> LCN </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="cash"> <i class="fas fa-money-bill"></i> Cash </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="transfer"> <i class="fas fa-exchange-alt"></i> Transfer </a> </div> </div> </div> <!-- Tabs Navigation --> <ul class="nav nav-tabs" id="receiptTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active" id="checks-tab" data-toggle="tab" href="#checks" role="tab"> <i class="fas fa-money-check"></i> Checks </a> </li> <li class="nav-item"> <a class="nav-link" id="lcns-tab" data-toggle="tab" href="#lcns" role="tab"> <i class="fas fa-file-invoice-dollar"></i> LCNs </a> </li> <li class="nav-item"> <a class="nav-link" id="cash-tab" data-toggle="tab" href="#cash" role="tab"> <i class="fas fa-money-bill"></i> Cash </a> </li> <li class="nav-item"> <a class="nav-link" id="transfers-tab" data-toggle="tab" href="#transfers" role="tab"> <i class="fas fa-exchange-alt"></i> Transfers </a> </li> </ul> <!-- Tab Content --> <div class="tab-content mt-4" id="receiptTabsContent"> <!-- Checks Tab --> <div class="tab-pane fade show active" id="checks" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Check Number</th> <th>Bank</th> <th>Due Date</th> <th>Amount</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for check in receipts.checks %} <tr> <td>{{ check.operation_date|date:"Y-m-d" }}</td> <td>{{ check.client.name }}</td> <td>{{ check.check_number }}</td> <td>{{ check.bank_name }}</td> <td>{{ check.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ check.amount|floatformat:2 }}</td> <td> <span class="badge {% if check.status == 'PORTFOLIO' %}badge-primary{% elif check.status == 'PAID' %}badge-success{% elif check.status == 'REJECTED' %}badge-danger{% else %}badge-warning{% endif %}"> {{ check.get_status_display }} </span> </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="check" data-action="edit" data-id="{{ check.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="check" data-id="{{ check.id }}"> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No checks found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- LCNs Tab --> <div class="tab-pane fade" id="lcns" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>LCN Number</th> <th>Issuing Bank</th> <th>Due Date</th> <th>Amount</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for lcn in receipts.lcns %} <tr> <td>{{ lcn.operation_date|date:"Y-m-d" }}</td> <td>{{ lcn.client.name }}</td> <td>{{ lcn.lcn_number }}</td> <td>{{ lcn.issuing_bank }}</td> <td>{{ lcn.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ lcn.amount|floatformat:2 }}</td> <td> <span class="badge {% if lcn.status == 'PORTFOLIO' %}badge-primary{% elif lcn.status == 'PAID' %}badge-success{% elif lcn.status == 'REJECTED' %}badge-danger{% else %}badge-warning{% endif %}"> {{ lcn.get_status_display }} </span> </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="lcn" data-action="edit" data-id="{{ lcn.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="lcn" data-id="{{ lcn.id }}"> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No LCNs found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Cash Tab --> <div class="tab-pane fade" id="cash" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Reference</th> <th>Credited Account</th> <th>Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for cash in receipts.cash %} <tr> <td>{{ cash.operation_date|date:"Y-m-d" }}</td> <td>{{ cash.client.name }}</td> <td>{{ cash.reference_number }}</td> <td>{{ cash.credited_account.bank }} - {{ cash.credited_account.account_number }}</td> <td class="text-right">{{ cash.amount|floatformat:2 }}</td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="cash" data-action="edit" data-id="{{ cash.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="cash" data-id="{{ cash.id }}"> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="6" class="text-center">No cash receipts found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Transfers Tab --> <div class="tab-pane fade" id="transfers" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Transfer Reference</th> <th>Transfer Date</th> <th>Credited Account</th> <th>Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for transfer in receipts.transfers %} <tr> <td>{{ transfer.operation_date|date:"Y-m-d" }}</td> <td>{{ transfer.client.name }}</td> <td>{{ transfer.transfer_reference }}</td> <td>{{ transfer.transfer_date|date:"Y-m-d" }}</td> <td>{{ transfer.credited_account.bank }} - {{ transfer.credited_account.account_number }}</td> <td class="text-right">{{ transfer.amount|floatformat:2 }}</td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="transfer" data-action="edit" data-id="{{ transfer.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="transfer" data-id="{{ transfer.id }}"> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="7" class="text-center">No transfers found</td> </tr> {% endfor %} </tbody> </table> </div> </div> </div> </div> </div> <!-- Receipt Modal --> <div class="modal fade" id="receiptModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Modal content will be loaded dynamically --> </div> </div> </div> <script> console.log("Extra JS loaded"); $(document).ready(function() { $('#receiptModal').on('show.bs.modal', function(e) { const button = $(e.relatedTarget); const type = button.data('type'); const action = button.data('action'); const id = button.data('id'); let url = ''; if (action === 'edit') { url += `edit/${type}/${id}/`; } else { url += `create/${type}/`; } // Load modal content $.get(url, function(data) { $('#receiptModal .modal-content').html(data); initializeForm(); if (action === 'edit') { // Set form action URL for edit $('#receiptForm').attr('action', url); // Initialize Select2 with pre-selected values if (data.client) { const clientOption = new Option(data.client.text, data.client.id, true, true); $('#client').append(clientOption).trigger('change'); } if (data.entity) { const entityOption = new Option(data.entity.text, data.entity.id, true, true); $('#entity').append(entityOption).trigger('change'); } } }); }); // Handle form submission for both create and edit $(document).on('submit', '#receiptForm', function(e) { e.preventDefault(); const form = $(this); const url = form.attr('action'); const isEdit = url.includes('/edit/'); $.ajax({ url: url, type: 'POST', data: form.serialize(), success: function(response) { if (response.status === 'success') { $('#receiptModal').modal('hide'); showToast(response.message, 'success'); location.reload(); // Refresh to show updated data } else { showFormErrors(form, response.errors); } }, error: function(xhr) { try { const errors = JSON.parse(xhr.responseText); showFormErrors(form, errors); } catch (e) { showToast('An error occurred while saving the receipt.', 'error'); } } }); }); function showFormErrors(form, errors) { // Clear previous errors form.find('.is-invalid').removeClass('is-invalid'); form.find('.invalid-feedback').remove(); // Show new errors Object.keys(errors).forEach(field => { const input = form.find(`[name="${field}"]`); const error = errors[field].join(' '); input.addClass('is-invalid'); input.after(`<div class="invalid-feedback">${error}</div>`); }); } function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">Notification</strong> <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> <div class="toast-body">${message}</div> </div> `; const toastContainer = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>'); toastContainer.html(toast); $('body').append(toastContainer); $('.toast').toast('show'); // Remove toast after it's hidden $('.toast').on('hidden.bs.toast', function() { $(this).closest('.toast-container').remove(); }); } }); // Initialize form elements after modal load function initializeForm() { console.log('Initializing form with autocomplete...'); console.log('Client input exists:', $('#client').length); console.log('Entity input exists:', $('#entity').length); // Initialize client autocomplete $("#client").autocomplete({ minLength: 2, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 2, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Add some basic styling to autocomplete dropdown $(".ui-autocomplete").addClass("dropdown-menu").css({ 'max-height': '200px', 'overflow-y': 'auto', 'overflow-x': 'hidden', 'z-index': '9999' }); } // Handle delete $('.delete-receipt').click(function() { if (confirm('Are you sure you want to delete this receipt?')) { const type = $(this).data('type'); const id = $(this).data('id'); $.ajax({ url: `/testapp/receipts/delete/${type}/${id}/`, type: 'POST', headers: { 'X-CSRFToken': '{{ csrf_token }}' }, success: function() { location.reload(); }, error: function() { alert('Error deleting receipt'); } }); } }); // Keyboard shortcuts $(document).keydown(function(e) { // Only trigger if no modal is open and no input is focused if ($('.modal:visible').length === 0 && !$(document.activeElement).is('input, textarea, select')) { let receiptType = null; if (e.altKey) { switch(e.key.toLowerCase()) { case 'c': // Alt + C for Check receiptType = 'check'; break; case 'l': // Alt + L for LCN receiptType = 'lcn'; break; case 'm': // Alt + M for Cash (Money) receiptType = 'cash'; break; case 't': // Alt + T for Transfer receiptType = 'transfer'; break; } if (receiptType) { e.preventDefault(); const url = "{% url 'receipt-create' 'TYPE' %}".replace('TYPE', receiptType); const modal = $('#receiptModal'); modal.modal('show'); modal.find('.modal-content').load(url, function() { setTimeout(function() { initializeForm(); }, 100); }); } } } }); // Add tooltip hints for shortcuts $('[data-toggle="modal"][data-target="#receiptModal"]').each(function() { const type = $(this).data('type'); let shortcut = ''; switch(type) { case 'check': shortcut = 'Alt+C'; break; case 'lcn': shortcut = 'Alt+L'; break; case 'cash': shortcut = 'Alt+M'; break; case 'transfer': shortcut = 'Alt+T'; break; } if (shortcut) { $(this).attr('title', `${$(this).text().trim()} (${shortcut})`); } }); </script> {% endblock %}
```

# templates/supplier/supplier_confirm_delete.html

```html
{% extends 'base.html' %} {% block title %}Delete Supplier{% endblock %} {% block content %} <h1>Delete Supplier</h1> <p>Are you sure you want to delete "{{ supplier.name }}"?</p> <form method="post"> {% csrf_token %} <button type="submit" class="btn btn-danger">Confirm Deletion</button> <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a> </form> {% endblock %}
```

# templates/supplier/supplier_form.html

```html
{% extends 'base.html' %} {% block title %}Supplier Form{% endblock %} {% block content %} <h1>{{ view.object.pk|default:'Add New Supplier' }}</h1> <form method="post"> {% csrf_token %} {{ form.as_p }} <button type="submit" class="btn btn-success">Save</button> <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a> </form> {% endblock %}
```

# templates/supplier/supplier_list.html

```html
{% extends 'base.html' %} {% block title %}Supplier List{% endblock %} {% block content %} <h1>Supplier List</h1> <a href="{% url 'supplier-create' %}" class="btn btn-primary">Add New Supplier</a> <table class="table mt-4"> <thead> <tr> <th>Name</th> <th>IF Code</th> <th>ICE Code</th> <th>RC Code</th> <th>Actions</th> </tr> </thead> <tbody> {% for supplier in suppliers %} <tr> <td>{{ supplier.name }}</td> <td>{{ supplier.if_code }}</td> <td>{{ supplier.ice_code }}</td> <td>{{ supplier.rc_code }}</td> <td> <a href="{% url 'supplier-update' supplier.pk %}" class="btn btn-warning">Edit</a> <a href="{% url 'supplier-delete' supplier.pk %}" class="btn btn-danger">Delete</a> </td> </tr> {% empty %} <tr> <td colspan="5">No suppliers found.</td> </tr> {% endfor %} </tbody> </table> {% endblock %}
```

# templatetags/__init__.py

```py

```

# templatetags/accounting_filters.py

```py
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def sum_debit(entries):
    return sum(entry['debit'] or 0 for entry in entries)

@register.filter
def sum_credit(entries):
    return sum(entry['credit'] or 0 for entry in entries)

@register.filter
def space_thousands(value):
    """
    Formats a number with spaces as thousand separators and 2 decimal places
    Example: 1234567.89 becomes 1 234 567.89
    """
    if value is None:
        return ''
    
    # Format to 2 decimal places first
    formatted = floatformat(value, 2)
    
    # Split the number into integer and decimal parts
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
    else:
        integer_part, decimal_part = formatted, '00'

    # Add space thousand separators to integer part
    int_with_spaces = ''
    for i, digit in enumerate(reversed(integer_part)):
        if i and i % 3 == 0:
            int_with_spaces = ' ' + int_with_spaces
        int_with_spaces = digit + int_with_spaces

    return f'{int_with_spaces}.{decimal_part}'
```

# templatetags/check_tags.py

```py
from django import template

register = template.Library()

@register.filter
def status_badge(status):
    return {
        'pending': 'secondary',
        'delivered': 'warning',
        'paid': 'success',
        'cancelled': 'danger'
    }.get(status, 'secondary')
```

# templatetags/custom_filters.py

```py
from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

```

# tests.py

```py
from django.test import TestCase

# Create your tests here.

```

# urls.py

```py
from django.urls import path, include
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
    CheckerFilterView, CheckFilterView, CheckDetailView, AvailableCheckersView, CheckerSignatureView, CheckerPositionStatusView
)

from .views_credit_notes import CreditNoteDetailsView, CreateCreditNoteView

from .views_bank import (
    BankAccountListView, BankAccountCreateView, 
    BankAccountDeactivateView, BankAccountFilterView,
    bank_account_autocomplete
)

from .views_receipts import (
    ReceiptListView, ReceiptCreateView, ReceiptUpdateView, ReceiptDeleteView, ReceiptDetailView, client_autocomplete, entity_autocomplete)

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
    list_entities,
    create_entity,
    update_entity,
    delete_entity
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
    path('checkers/<uuid:pk>/signatures/', CheckerSignatureView.as_view(), name='checker-signatures'),
    path('checkers/<uuid:pk>/sign/', CheckerSignatureView.as_view(), name='checker-sign'),
    path('checkers/<uuid:checker_id>/position-status/<int:position>/',
    CheckerPositionStatusView.as_view(),
    name='checker-position-status'),

    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/create/', BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<uuid:pk>/deactivate/', 
         BankAccountDeactivateView.as_view(), name='bank-account-deactivate'),
    path('bank-accounts/filter/', 
         BankAccountFilterView.as_view(), name='bank-account-filter'),
    path('bank-accounts/', bank_account_autocomplete, name='bank_account_autocomplete'),

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

    # Autocomplete endpoints for form fields
    path('receipts/client/autocomplete', client_autocomplete, name='client-autocomplete'),
    path('receipts/entity/autocomplete', entity_autocomplete, name='entity-autocomplete'),



    

]


```

# views_bank.py

```py
from django.views.generic import ListView, View
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import BankAccount
from django.contrib import messages
import json
from django.core.exceptions import ValidationError

class BankAccountListView(ListView):
    model = BankAccount
    template_name = 'bank/bank_list.html'
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = BankAccount.BANK_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters if any
        bank = self.request.GET.get('bank')
        if bank:
            queryset = queryset.filter(bank=bank)
            
        account_type = self.request.GET.get('type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(is_active=status == 'active')
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(account_number__icontains=search)
            
        return queryset

class BankAccountCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Basic validation
            required_fields = ['bank', 'account_number', 'accounting_number', 
                             'journal_number', 'city', 'account_type']
            
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse(
                        {'error': f'{field.replace("_", " ").title()} is required'}, 
                        status=400
                    )
            
            # Specific validations
            if not data['account_number'].isdigit() or len(data['account_number']) < 10:
                return JsonResponse(
                    {'error': 'Account number must be at least 10 digits'}, 
                    status=400
                )
                
            if not data['accounting_number'].isdigit() or len(data['accounting_number']) < 5:
                return JsonResponse(
                    {'error': 'Accounting number must be at least 5 digits'}, 
                    status=400
                )
                
            if not data['journal_number'].isdigit() or len(data['journal_number']) != 2:
                return JsonResponse(
                    {'error': 'Journal number must be exactly 2 digits'}, 
                    status=400
                )

            # Create account
            account = BankAccount.objects.create(**data)
            
            return JsonResponse({
                'message': 'Bank account created successfully',
                'id': str(account.id)
            })
            
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class BankAccountDeactivateView(View):
    def post(self, request, pk):
        try:
            account = BankAccount.objects.get(pk=pk)
            
            # Check for active checkers
            if account.checker_set.filter(is_active=True).exists():
                return JsonResponse(
                    {'error': 'Cannot deactivate account with active checkers'}, 
                    status=400
                )
            
            account.is_active = False
            account.save()
            
            return JsonResponse({'message': 'Account deactivated successfully'})
            
        except BankAccount.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class BankAccountFilterView(View):
    def get(self, request):
        try:
            # Start with all accounts
            queryset = BankAccount.objects.all()
            print("Initial QuerySet Count:", queryset.count())  # Debug log
            
            # Apply bank filter
            bank = request.GET.get('bank')
            if bank:
                print("Filter by bank:", bank)  # Debug log
                queryset = queryset.filter(bank=bank)

            # Apply account type filter
            account_type = request.GET.get('type')
            if account_type:
                print("Filter by account type:", account_type)  # Debug log
                queryset = queryset.filter(account_type=account_type)

            # Apply status filter
            status = request.GET.get('status')
            if status:
                print("Filter by status:", status)  # Debug log
                queryset = queryset.filter(is_active=status == 'active')

            # Apply search filter
            search = request.GET.get('search')
            if search:
                print("Filter by search term:", search)  # Debug log
                queryset = queryset.filter(account_number__icontains=search)

            # Final count before rendering
            print("Filtered QuerySet Count:", queryset.count())  # Debug log

            # Render rows
            html = render_to_string(
                'bank/partials/accounts_table.html',
                {'accounts': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            print("Error in filter view:", str(e))  # Debug log
            return JsonResponse({'error': str(e)}, status=500)



def bank_account_autocomplete(request):
    search_term = request.GET.get('search', '')
    accounts = BankAccount.objects.filter(account_number__icontains=search_term)[:10]
    results = [
        {
            "label": f"{account.bank} [{account.account_number}]",
            "value": account.id,
            "bank": account.bank
        }
        for account in accounts
    ]
    return JsonResponse(results, safe=False)
```

# views_checkers.py

```py
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Checker, Check, Invoice, Supplier, BankAccount
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from dateutil.parser import parse
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal




class CheckerListView(ListView):
    model = Checker
    template_name = 'checker/checker_list.html'
    context_object_name = 'checkers'

    def get_queryset(self):
        return Checker.objects.select_related('bank_account').filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = BankAccount.objects.filter(
            is_active=True,
            account_type='national'
        )

        # Precompute additional fields for checkers
        for checker in context['checkers']:
            checker.remaining_ratio = f"{checker.remaining_pages}/{checker.num_pages}"
            checker.remaining_percentage = (
                (checker.remaining_pages / checker.num_pages) * 100 if checker.num_pages > 0 else 0
            )

        print("Banks available:", context['banks'])
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CheckerCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate bank account
            bank_account = get_object_or_404(
                BankAccount, 
                id=data['bank_account_id'],
                is_active=True,
                account_type='national'
            )

            # Create checker
            checker = Checker.objects.create(
                type=data['type'],
                bank_account=bank_account,
                num_pages=int(data['num_pages']),
                index=data['index'].upper(),
                starting_page=int(data['starting_page'])
            )
            
            return JsonResponse({
                'message': 'Checker created successfully',
                'checker': {
                    'id': str(checker.id),
                    'code': checker.code,
                    'current_position': checker.current_position,
                    'final_page': checker.final_page
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckerDetailsView(View):
    def get(self, request, pk):
        try:
            checker = get_object_or_404(Checker, pk=pk)
            
            # Get all used positions
            used_positions = set(
                checker.checks.values_list('position', flat=True)
            )
            
            # Calculate available positions
            available_positions = [
                pos for pos in range(checker.starting_page, checker.final_page + 1)
                if str(pos) not in used_positions
            ]
            
            # Find first available position
            next_available = min(available_positions) if available_positions else None
            
            return JsonResponse({
                'id': str(checker.id),
                'starting_page': checker.starting_page,
                'final_page': checker.final_page,
                'current_position': checker.current_position,
                'remaining_pages': checker.remaining_pages,
                'used_positions': list(used_positions),
                'available_positions': available_positions,
                'next_available': next_available,
                'status': checker.status
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class CheckerDeleteView(View):
    def post(self, request, pk):
        try:
            checker = get_object_or_404(Checker, pk=pk)
            if checker.checks.exists():
                return JsonResponse({'error': 'Cannot delete checker with existing checks'}, status=400)
            checker.delete()
            return JsonResponse({'message': 'Checker deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class AvailableCheckersView(View):
    def get(self, request):
        try:
            # Add debug print
            print("Starting AvailableCheckersView get request")
            
            checkers = Checker.objects.filter(
                is_active=True
            ).exclude(
                status='completed'
            ).select_related('bank_account')
            
            # Debug print the queryset
            print(f"Found {checkers.count()} checkers")
            
            checker_data = [{
                'id': str(checker.id),
                'bank': checker.bank_account.get_bank_display(),
                'account': checker.bank_account.account_number,
                'remaining_pages': checker.remaining_pages,
                'label': f"{checker.bank_account.get_bank_display()} - {checker.bank_account.account_number} ({checker.remaining_pages} pages)"
            } for checker in checkers]
            
            print(f"Processed {len(checker_data)} checkers into data")

            return JsonResponse({
                'checkers': checker_data
            })

        except Exception as e:
            # Enhanced error reporting
            print(f"Exception type: {type(e)}")
            print(f"Exception args: {e.args}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({'error': str(e)}, status=400)


def invoice_autocomplete(request):
    query = request.GET.get('term', '')
    supplier_id = request.GET.get('supplier')
    
    invoices = Invoice.objects.filter(
        supplier_id=supplier_id,
        ref__icontains=query,
        type='invoice'
    )
    
    invoice_list = []
    for invoice in invoices:
        net_amount = float(invoice.net_amount)
        checks_amount = float(sum(
            check.amount
        for check in Check.objects.filter(
                        cause=invoice
                    ).exclude(
                        status='cancelled'
                    )
        ) or 0)
        
        # Calculate available amount
        available_amount = max(0, net_amount - checks_amount)
        
        # Skip invoices that are fully paid or have no remaining amount
        if available_amount <= 0:
            continue

        status_icon = {
            'paid': '🔒 Paid',
            'partially_paid': '⏳ Partially Paid',
            'not_paid': '📄 Not Paid'
        }.get(invoice.payment_status, '')

        credit_note_info = ""
        if invoice.has_credit_notes:
            credit_note_info = f" (Credited: {float(invoice.total_amount - invoice.net_amount):,.2f})"
        
        invoice_list.append({
            'id': str(invoice.id),
            'ref': invoice.ref,
            'date': invoice.date.strftime('%Y-%m-%d'),
            'status': status_icon,
            'amount': net_amount,
            'payment_info': {
                'total_amount': net_amount,  # Use net amount instead of total
                'issued_amount': float(checks_amount),
                'paid_amount': float(sum(
                    check.amount for check in Check.objects.filter(
                        cause=invoice,
                        status='paid'
                    )
                )),
                'available_amount': available_amount
            },
            'label': (
                f"{invoice.ref} ({invoice.date.strftime('%Y-%m-%d')}) - "
                f"{status_icon} - {net_amount:,.2f} MAD{credit_note_info}"
            )
        })
    
    return JsonResponse(invoice_list, safe=False)

class CheckerSignatureView(View):
    def get(self, request, pk):
        checker = get_object_or_404(Checker, pk=pk)
        print(f"Getting signatures for checker {pk}")
        
        used_positions = {
            str(check.position): {
                'ref': check.position,
                'beneficiary': check.beneficiary.name if check.beneficiary else None,
                'amount': float(check.amount) if check.amount else None
            }
            for check in checker.checks.exclude(status='available')
        }
        print(f"Used positions: {used_positions}")
        
        return JsonResponse({
            'positions': checker.position_signatures,
            'used_positions': used_positions
        })

    def post(self, request, pk):
        checker = get_object_or_404(Checker, pk=pk)
        position = request.POST.get('position')
        signature = request.POST.get('signature')
        
        print(f"Adding signature {signature} to position {position}")
        checker.add_signature(position, signature)
        
        return JsonResponse({'status': 'success'})
    
class CheckerPositionStatusView(View):
    def get(self, request, checker_id, position):
        print(f"Checking status for position {position} in checker {checker_id}")
        checker = get_object_or_404(Checker, pk=checker_id)
        
        # Format full position with index
        full_position = position
        print(f"Checking full position: {full_position}")
        
        is_used = checker.checks.filter(
            position=full_position
        ).exists()
        
        print(f"Position {full_position} used status: {is_used}")
        return JsonResponse({
            'is_used': is_used,
            'full_position': full_position
        })

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            print("Raw request body:", request.body)  # Debug raw request
            data = json.loads(request.body)
            print("Parsed JSON data:", data)  # Debug parsed data
            
            position = data.get('position')
            print("Position value:", position, "Type:", type(position))
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            invoice = get_object_or_404(Invoice, pk=data['invoice_id'])

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            
            check = Check.objects.create(
                position= position,
                checker=checker,
                creation_date=data.get('creation_date', timezone.now().date()),
                beneficiary=invoice.supplier,
                cause=invoice,
                payment_due=payment_due,
                amount_due=invoice.total_amount,
                amount=data['amount'],
                observation=data.get('observation', '')
            )
            
            return JsonResponse({
                'message': 'Check created successfully',
                'check_id': str(check.id)
            })
            
        except Exception as e:
            print("Error creating check:", str(e))  # Debug print
            return JsonResponse({'error': str(e)}, status=400)
    
class CheckListView(ListView):
    model = Check
    template_name = 'checker/check_list.html'
    context_object_name = 'checks'

    def get_queryset(self):
        return Check.objects.select_related(
            'checker__bank_account', 
            'beneficiary', 
            'cause'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get distinct banks that have checks
        context['banks'] = BankAccount.objects.filter(
            checker__checks__isnull=False
        ).distinct()
        context['rejection_reasons'] = Check.REJECTION_REASONS
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CheckStatusView(View):
    def post(self, request, pk, action):
        try:
            check = get_object_or_404(Check, pk=pk)
            
            if action == 'delivered':
                if check.delivered:
                    return JsonResponse({'error': 'Check already delivered'}, status=400)
                check.delivered = True
            elif action == 'paid':
                if not check.delivered:
                    return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                if check.paid:
                    return JsonResponse({'error': 'Check already paid'}, status=400)
                check.paid = True
            
            check.save()
            return JsonResponse({'message': f'Check marked as {action}'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def supplier_autocomplete(request):
    query = request.GET.get('term', '')
    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) | 
        Q(accounting_code__icontains=query)
    )[:10]
    
    supplier_list = [{
        "label": f"{supplier.name} ({supplier.accounting_code})",
        "value": str(supplier.id)
    } for supplier in suppliers]
    
    return JsonResponse(supplier_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckUpdateView(View):
    def get(self, request, pk):
        try:
            check = get_object_or_404(Check, pk=pk)
            return JsonResponse({
                'id': str(check.id),
                'status': check.status,
                'delivered_at': check.delivered_at.strftime('%Y-%m-%dT%H:%M') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%dT%H:%M') if check.paid_at else None,
                'cancelled_at': check.cancelled_at.strftime('%Y-%m-%dT%H:%M') if check.cancelled_at else None,
                'cancellation_reason': check.cancellation_reason
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if 'delivered_at' in data:
                check.delivered_at = parse(data['delivered_at']) if data['delivered_at'] else None
                check.delivered = bool(check.delivered_at)
                if check.delivered_at:
                    check.status = 'delivered'
            
            if 'paid_at' in data:
                if data['paid_at'] and not check.delivered_at:
                    return JsonResponse({'error': 'Check must be delivered before being marked as paid'}, status=400)
                check.paid_at = parse(data['paid_at']) if data['paid_at'] else None
                check.paid = bool(check.paid_at)
                if check.paid_at:
                    check.status = 'paid'
            
            check.save()
            return JsonResponse({'message': 'Check updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class CheckCancelView(View):
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if check.paid_at:
                return JsonResponse({'error': 'Cannot cancel a paid check'}, status=400)
                
            check.cancelled_at = timezone.now()
            check.cancellation_reason = data.get('reason')
            check.status = 'cancelled'
            check.save()
            
            return JsonResponse({'message': 'Check cancelled successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class CheckActionView(View):
    def post(self, request, pk):
            try:
                check = get_object_or_404(Check, pk=pk)
                data = json.loads(request.body)
                action = data.get('action')
                print(f"Action received: {action}")  # Debug
                print(f"Request data: {data}")  # Debug

                if action == 'print':
                    if check.status == 'draft':
                        check.status = 'printed'
                        check.save()
                elif action == 'sign':
                    signature = data.get('signature')
                    if check.can_be_signed(signature):
                        check.add_signature(signature)                
                elif action == 'reject':
                    reason = data.get('rejection_reason')
                    notes = data.get('rejection_note')
                    print(f"Rejection reason: {reason}")  # Debug
                    print(f"Rejection notes: {notes}")  # Debug
                    check.rejected_at = timezone.now()
                    check.rejection_reason = reason
                    check.rejection_note = notes
                    check.status = 'rejected'
                    print(f"Check status after update: {check.status}")  # Debug

                elif action == 'receive':
                    check.receive(notes=data.get('notes', ''))

                elif action == 'replace':
                    if not check.can_be_replaced:
                        raise ValidationError("Cannot replace this check")
                    
                    # Get the new checker
                    checker = get_object_or_404(Checker, pk=data.get('checker_id'))
                    
                    # Pass checker as a named argument
                    replacement = check.create_replacement(
                    checker=checker,  # Fix is here - pass checker as named arg
                    amount=Decimal(data.get('amount')),
                    payment_due=data.get('payment_due') or None,  # Handle empty string
                    observation=data.get('observation', '')
                            )

                elif action == 'cancel':
                    reason = data.get('reason')
                    if not reason:
                        return JsonResponse({'error': 'Reason is required'}, status=400)
                    check.cancelled_at = timezone.now()
                    check.cancellation_reason = reason
                    check.status = 'cancelled'

                elif action == 'deliver':
                    check.delivered_at = timezone.now()
                    check.status = 'delivered'

                elif action == 'pay':
                    if not check.delivered_at:
                        return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                    check.paid_at = timezone.now()
                    check.status = 'paid'

                check.save()
                return JsonResponse({'status': 'success'})

            except Check.DoesNotExist:
                return JsonResponse({'error': 'Check not found'}, status=404)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            except Exception as e:
                print(f"Error handling check action: {str(e)}")  # Debug
                return JsonResponse({'error': str(e)}, status=500)

class CheckerFilterView(View):
    def get(self, request):
        queryset = Checker.objects.all()
        
        bank_account = request.GET.get('bank_account')
        if bank_account:
            queryset = queryset.filter(bank_account_id=bank_account)
            
        checker_type = request.GET.get('type')
        if checker_type:
            queryset = queryset.filter(type=checker_type)
            
        status = request.GET.get('status')
        if status:
            if status == 'New':
                queryset = queryset.filter(current_position__lt=F('final_page'))
            elif status == 'Completed':
                queryset = queryset.filter(current_position=F('final_page'))

        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(index__icontains=search)
            )

        html = render_to_string(
            'checker/partials/checkers_table.html',
            {'checkers': queryset},
            request=request
        )
        
        return JsonResponse({'html': html})

class CheckFilterView(View):
    def get(self, request):
        try:
            queryset = Check.objects.select_related(
                'checker__bank_account',
                'beneficiary',
                'cause'
            )

            # Apply bank filter
            if bank := request.GET.get('bank'):
                queryset = queryset.filter(checker__bank_account__bank=bank)
                
            # Apply status filter
            if status := request.GET.get('status'):
                queryset = queryset.filter(status=status)
                
            # Apply beneficiary filter
            if beneficiary := request.GET.get('beneficiary'):
                queryset = queryset.filter(beneficiary_id=beneficiary)
                
            # Apply search
            if search := request.GET.get('search'):
                queryset = queryset.filter(
                    Q(position__icontains=search) |
                    Q(beneficiary__name__icontains=search) |
                    Q(cause__ref__icontains=search)
                )

            # Render partial template
            html = render_to_string(
                'checker/partials/checks_table.html',
                {'checks': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class CheckDetailView(View):
    def get(self, request, check_id):
        try:
            check = Check.objects.get(id=check_id)
            data = {
                "creation_date": check.creation_date.strftime("%Y-%m-%d") if check.creation_date else None,
                "delivered_at": check.delivered_at.strftime("%Y-%m-%d") if check.delivered_at else None,
                "paid_at": check.paid_at.strftime("%Y-%m-%d") if check.paid_at else None,
                "rejected_at": check.rejected_at.strftime("%Y-%m-%d") if check.rejected_at else None,
                "rejection_reason": check.rejection_reason,
                "rejection_note": check.rejection_note,
                "cancelled_at": check.cancelled_at.strftime("%Y-%m-%d") if check.cancelled_at else None,
                "cancellation_reason": check.cancellation_reason,
                "received_at": check.received_at.strftime("%Y-%m-d") if check.received_at else None,
                "received_notes": check.received_notes,
                "reference": f"{check.checker.bank_account.bank}-{check.position}",
                "amount": float(check.amount),
                "replacement_info": {
                "replaces": {
                    "id": str(check.replaces.id),
                    "reference": f"{check.replaces.checker.bank_account.bank}-{check.replaces.position}",
                    "amount": float(check.replaces.amount),
                    "rejection_reason": check.replaces.rejection_reason,
                    "rejection_date": check.replaces.rejected_at.strftime("%Y-%m-%d") if check.replaces.rejected_at else None
                } if check.replaces else None,
                "replaced_by": {
                    "id": str(check.replaced_by.first().id),
                    "reference": f"{check.replaced_by.first().checker.bank_account.bank}-{check.replaced_by.first().position}",
                    "amount": float(check.replaced_by.first().amount),
                    "date": check.replaced_by.first().created_at.strftime("%Y-%m-%d")
                } if check.replaced_by.exists() else None
            }
                
            }
            return JsonResponse(data)
        except Check.DoesNotExist:
            return JsonResponse({"error": "Check not found"}, status=404)
```

# views_client.py

```py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from .models import Client, Entity, ClientSale
import json
import logging
from django.views.generic import ListView, DetailView
from django.utils import timezone
import calendar
from django.db.models import Q

# Configure logger
logger = logging.getLogger(__name__)

def client_management(request):
    """Main view for client management interface"""
    logger.info("Accessing client management page")
    return render(request, 'client/client_management.html')

@require_http_methods(["GET"])
def list_clients(request):
    """API endpoint to list all clients"""
    logger.debug("Fetching client list")
    try:
        clients = Client.objects.all()
        data = [{
            'id': str(c.id),
            'name': c.name,
            'client_code': c.client_code
        } for c in clients]
        logger.info(f"Successfully fetched {len(data)} clients")
        return JsonResponse({'clients': data})
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_client(request):
    """API endpoint to create a new client"""
    logger.debug("Creating new client")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Validate client code format
        client_code = data.get('client_code', '').strip()
        if not client_code.isdigit() or len(client_code) < 5 or len(client_code) > 10:
            raise ValidationError("Invalid client code format")
        
        # Check for duplicate client code
        if Client.objects.filter(client_code=client_code).exists():
            raise ValidationError("Client code already exists")
        
        client = Client.objects.create(
            name=data['name'],
            client_code=client_code
        )
        logger.info(f"Successfully created client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        }, status=201)
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_client(request, client_id):
    """API endpoint to update a client"""
    logger.debug(f"Updating client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Update fields
        client.name = data['name']
        if 'client_code' in data:
            new_code = data['client_code'].strip()
            if not new_code.isdigit() or len(new_code) < 5 or len(new_code) > 10:
                raise ValidationError("Invalid client code format")
            if Client.objects.filter(client_code=new_code).exclude(id=client_id).exists():
                raise ValidationError("Client code already exists")
            client.client_code = new_code
            
        client.save()
        logger.info(f"Successfully updated client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_client(request, client_id):
    """API endpoint to delete a client"""
    logger.debug(f"Deleting client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        logger.info(f"Successfully deleted client: {client.name}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def validate_field(request, field, value):
    """API endpoint to validate unique fields"""
    logger.debug(f"Validating {field}: {value}")
    
    # Handle empty values
    if not value or value.strip() == '':
        return JsonResponse({'error': 'Value cannot be empty'}, status=400)
    
    try:
        if field == 'clientCode':
            if not (5 <= len(value) <= 10):
                return JsonResponse({'error': 'Client code must be between 5 and 10 digits'}, status=400)
            exists = Client.objects.filter(client_code=value).exists()
        elif field == 'accountingCode':
            if not (5 <= len(value) <= 7):
                return JsonResponse({'error': 'Accounting code must be between 5 and 7 digits'}, status=400)
            if not value.startswith('3'):
                return JsonResponse({'error': 'Accounting code must start with 3'}, status=400)
            exists = Entity.objects.filter(accounting_code=value).exists()
        elif field == 'iceCode':
            if len(value) != 15:
                return JsonResponse({'error': 'ICE code must be exactly 15 digits'}, status=400)
            exists = Entity.objects.filter(ice_code=value).exists()
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        return JsonResponse({'available': not exists})
    except Exception as e:
        logger.error(f"Error validating {field}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
class ClientSaleListView(ListView):
    template_name = 'client/sale_list.html'
    model = ClientSale
    context_object_name = 'sales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = timezone.now().year
        context['current_month'] = timezone.now().month
        context['month_choices'] = [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]
        return context

@require_http_methods(["POST"])
def create_sale(request):
    try:
        data = request.POST
        sale = ClientSale.objects.create(
            client_id=data['client'],
            date=data['date'],
            amount=data['amount'],
            year=int(data.get('year') or data['date'][:4]),
            month=int(data.get('month') or data['date'][5:7]),
            notes=data.get('notes', '')
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Sale recorded successfully',
            'id': str(sale.id)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

class ClientCardView(DetailView):
    model = Client
    template_name = 'client/client_card.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get year and month from query params or use current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        try:
            year = int(year)
            month = int(month)
        except (TypeError, ValueError):
            year = timezone.now().year
            month = timezone.now().month

        # Get transactions for period
        transactions = self.object.get_transactions(year, month)
        
        context.update({
            'transactions': transactions,
            'selected_year': year,
            'selected_month': month,
            'years': range(2024, timezone.now().year + 1),
            'months': [
                (i, calendar.month_name[i]) 
                for i in range(1, 13)
            ],
            'total_debit': sum(t['debit'] or 0 for t in transactions),
            'total_credit': sum(t['credit'] or 0 for t in transactions),
            'final_balance': transactions[-1]['balance'] if transactions else 0,
        })
        
        return context
    
def client_autocomplete(request):
    term = request.GET.get('term', '')
    clients = Client.objects.filter(
        Q(name__icontains=term) |
        Q(client_code__icontains=term)
    )[:10]

    results = [{
        'id': str(client.id),
        'value': str(client.id),
        'label': f"{client.name} ({client.client_code})"
    } for client in clients]

    return JsonResponse(results, safe=False)
```

# views_credit_notes.py

```py
from django.views import View
from django.http import JsonResponse
from .models import Invoice, InvoiceProduct, Product
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CreditNoteDetailsView(View):
    def get(self, request, invoice_id):
        print("Credit note details requested for invoice:", invoice_id) 
        invoice = get_object_or_404(Invoice, id=invoice_id)
        credited_quantities = invoice.get_credited_quantities()
        available_quantities = invoice.get_available_quantities()
        
        products = []
        for item in invoice.products.all():
            products.append({
                'id': str(item.product.id),
                'name': item.product.name,
                'original_quantity': item.quantity,
                'credited_quantity': credited_quantities.get(item.product.id, 0),
                'available_quantity': available_quantities.get(item.product.id, 0),
                'unit_price': float(item.unit_price)
            })

        return JsonResponse({
            'invoice': {
                'ref': invoice.ref,
                'date': invoice.date.strftime('%Y-%m-d'),
                'total_amount': float(invoice.total_amount),
                'credited_amount': float(invoice.total_amount - invoice.net_amount)
            },
            'products': products
        })
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateCreditNoteView(View):
    def post(self, request):
        try:
            print("Received POST request for creating credit note")
            data = json.loads(request.body)
            print("Received data:", data)
            original_invoice = get_object_or_404(Invoice, id=data['original_invoice_id'])
            print("Original Invoice:", original_invoice)

            # Check for duplicate reference
            if Invoice.objects.filter(ref=data['ref']).exists():
                return JsonResponse(
                    {'error': 'Credit note reference already exists'}, 
                    status=400
                )
            
            # Create credit note
            credit_note = Invoice.objects.create(
                type='credit_note',
                original_invoice=original_invoice,
                supplier=original_invoice.supplier,
                ref=data['ref'],
                date=data['date'],
                status='draft'
            )

            # Add products
            for product_data in data['products']:
                product = get_object_or_404(Product, id=product_data['product_id'])
                original_item = original_invoice.products.get(product=product)
                
                InvoiceProduct.objects.create(
                    invoice=credit_note,
                    product=product,
                    quantity=product_data['quantity'],
                    unit_price=original_item.unit_price,
                    reduction_rate=original_item.reduction_rate,
                    vat_rate=original_item.vat_rate
                )

            return JsonResponse({
                'message': 'Credit note created successfully',
                'credit_note_id': str(credit_note.id)
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
```

# views_entity.py

```py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Entity, Client
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def list_entities(request):
    """API endpoint to list all entities"""
    logger.debug("Fetching entity list")
    try:
        entities = Entity.objects.all()
        data = [{
            'id': str(e.id),
            'name': e.name,
            'ice_code': e.ice_code,
            'accounting_code': e.accounting_code,
            'city': e.city,
            'phone_number': e.phone_number
        } for e in entities]
        logger.info(f"Successfully fetched {len(data)} entities")
        return JsonResponse({'entities': data})
    except Exception as e:
        logger.error(f"Error fetching entities: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_entity(request):
    """API endpoint to create a new entity"""
    logger.debug("Creating new entity")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")

        # Validate ICE code
        ice_code = data.get('ice_code', '').strip()
        if not ice_code.isdigit() or len(ice_code) != 15:
            raise ValidationError("Invalid ICE code format")

        # Validate accounting code
        accounting_code = data.get('accounting_code', '').strip()
        if not accounting_code.startswith('3') or not accounting_code.isdigit() or \
           len(accounting_code) < 5 or len(accounting_code) > 7:
            raise ValidationError("Invalid accounting code format")

        # Check for duplicates
        if Entity.objects.filter(ice_code=ice_code).exists():
            raise ValidationError("ICE code already exists")
        if Entity.objects.filter(accounting_code=accounting_code).exists():
            raise ValidationError("Accounting code already exists")

        entity = Entity.objects.create(
            name=data['name'],
            ice_code=ice_code,
            accounting_code=accounting_code,
            city=data.get('city', ''),
            phone_number=data.get('phone_number', '')
        )
        logger.info(f"Successfully created entity: {entity.name}")

        return JsonResponse({
            'id': str(entity.id),
            'name': entity.name,
            'ice_code': entity.ice_code,
            'accounting_code': entity.accounting_code,
            'city': entity.city,
            'phone_number': entity.phone_number
        }, status=201)

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_entity(request, entity_id):
    """API endpoint to update an entity"""
    logger.debug(f"Updating entity {entity_id}")
    try:
        entity = get_object_or_404(Entity, id=entity_id)
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")

        # Validate ICE code if provided
        if 'ice_code' in data:
            ice_code = data['ice_code'].strip()
            if not ice_code.isdigit() or len(ice_code) != 15:
                raise ValidationError("Invalid ICE code format")
            if Entity.objects.filter(ice_code=ice_code).exclude(id=entity_id).exists():
                raise ValidationError("ICE code already exists")
            entity.ice_code = ice_code

        # Validate accounting code if provided
        if 'accounting_code' in data:
            accounting_code = data['accounting_code'].strip()
            if not accounting_code.startswith('3') or not accounting_code.isdigit() or \
               len(accounting_code) < 5 or len(accounting_code) > 7:
                raise ValidationError("Invalid accounting code format")
            if Entity.objects.filter(accounting_code=accounting_code).exclude(id=entity_id).exists():
                raise ValidationError("Accounting code already exists")
            entity.accounting_code = accounting_code

        # Update other fields
        entity.name = data.get('name', entity.name)
        entity.city = data.get('city', entity.city)
        entity.phone_number = data.get('phone_number', entity.phone_number)

        entity.save()
        logger.info(f"Successfully updated entity: {entity.name}")

        return JsonResponse({
            'id': str(entity.id),
            'name': entity.name,
            'ice_code': entity.ice_code,
            'accounting_code': entity.accounting_code,
            'city': entity.city,
            'phone_number': entity.phone_number
        })

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_entity(request, entity_id):
    """API endpoint to delete an entity"""
    logger.debug(f"Deleting entity {entity_id}")
    try:
        entity = get_object_or_404(Entity, id=entity_id)
        entity.delete()
        logger.info(f"Successfully deleted entity: {entity.name}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    

@require_http_methods(["GET"])
def validate_field(request, field, value):
    """API endpoint to validate unique fields"""
    logger.debug(f"Validating {field}: {value}")
    
    # Handle empty values
    if not value or value.strip() == '':
        return JsonResponse({'error': 'Value cannot be empty'}, status=400)
    
    try:
        if field == 'clientCode':
            if not (5 <= len(value) <= 10):
                return JsonResponse({'error': 'Client code must be between 5 and 10 digits'}, status=400)
            exists = Client.objects.filter(client_code=value).exists()
        elif field == 'accountingCode':
            if not (5 <= len(value) <= 7):
                return JsonResponse({'error': 'Accounting code must be between 5 and 7 digits'}, status=400)
            if not value.startswith('3'):
                return JsonResponse({'error': 'Accounting code must start with 3'}, status=400)
            exists = Entity.objects.filter(accounting_code=value).exists()
        elif field == 'iceCode':
            if len(value) != 15:
                return JsonResponse({'error': 'ICE code must be exactly 15 digits'}, status=400)
            exists = Entity.objects.filter(ice_code=value).exists()
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        return JsonResponse({'available': not exists})
    except Exception as e:
        logger.error(f"Error validating {field}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
```

# views_invoice.py

```py
from django.urls import reverse_lazy
from django.db import models
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Invoice, InvoiceProduct, Product, ExportRecord, Check, Supplier
from .forms import InvoiceCreateForm, InvoiceUpdateForm  # Import the custom form here
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q,F, Case, When, DecimalField, Subquery, Sum, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.template.loader import render_to_string
from django.db.models.sql.where import EmptyResultSet



@method_decorator(csrf_exempt, name='dispatch')
class AddProductToInvoiceView(View):
    def post(self, request):
        invoice_id = request.POST.get('invoice_id')
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate', 0)  # Add default value
        expense_code = request.POST.get('expense_code')

        try:
            # Fetch the invoice and product
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            product = get_object_or_404(Product, pk=product_id)

            # Create a new InvoiceProduct entry
            invoice_product = InvoiceProduct.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                vat_rate=vat_rate,
                reduction_rate=reduction_rate
            )

            # Success response
            return JsonResponse({"message": "Product added successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# List all Invoices
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        queryset = Invoice.objects.all().select_related('supplier').prefetch_related('products')

        # Debug prints
        print("Request GET params:", self.request.GET)

        # Date Range Filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        try:
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
        except Exception as e:
            print(f"Error filtering by date range: {e}")

        # Amount Range Filter
        amount_min = self.request.GET.get('amount_min')
        amount_max = self.request.GET.get('amount_max')
        try:
            if amount_min or amount_max:
                invoices = list(queryset)  # Evaluate queryset into a list for manual filtering
                filtered_invoices = []

                amount_min = Decimal(amount_min if amount_min else '0')
                amount_max = Decimal(amount_max if amount_max else '999999999')

                for invoice in invoices:
                    net_amount = invoice.net_amount  # Assume net_amount is a computed property
                    if amount_min <= net_amount <= amount_max:
                        filtered_invoices.append(invoice.id)

                queryset = queryset.filter(id__in=filtered_invoices)
        except Exception as e:
            print(f"Error filtering by amount range: {e}")

        # Supplier Filter
        supplier = self.request.GET.get('supplier')
        try:
            if supplier:
                queryset = queryset.filter(supplier_id=supplier)
        except Exception as e:
            print(f"Error filtering by supplier: {e}")

        # Payment Status Filter
        payment_status = self.request.GET.get('payment_status')
        try:
            if payment_status:
                queryset = queryset.filter(payment_status=payment_status)
        except Exception as e:
            print(f"Error filtering by payment status: {e}")

        # Export Status Filter
        export_status = self.request.GET.get('export_status')
        try:
            if export_status == 'exported':
                queryset = queryset.filter(exported_at__isnull=False)
            elif export_status == 'not_exported':
                queryset = queryset.filter(exported_at__isnull=True)
        except Exception as e:
            print(f"Error filtering by export status: {e}")

        # Product Filter
        product_id = self.request.GET.get('product')
        try:
            if product_id:
                queryset = queryset.filter(products__product_id=product_id)
        except Exception as e:
            print(f"Error filtering by product: {e}")

        # Payment Status Filters
        try:
            has_pending_checks = self.request.GET.get('has_pending_checks')
            if has_pending_checks:
                queryset = queryset.filter(check__status='pending').distinct()

            has_delivered_unpaid = self.request.GET.get('has_delivered_unpaid')
            if has_delivered_unpaid:
                queryset = queryset.filter(check__status='delivered').exclude(check__status='paid').distinct()
        except Exception as e:
            print(f"Error filtering by payment status checks: {e}")

        # Energy Filter
        is_energy = self.request.GET.get('is_energy')
        try:
            if is_energy:
                queryset = queryset.filter(supplier__is_energy=True)
        except Exception as e:
            print(f"Error filtering by energy suppliers: {e}")

        # Credit Note Status
        credit_note_status = self.request.GET.get('credit_note_status')
        try:
            if credit_note_status == 'has_credit_notes':
                queryset = queryset.filter(credit_notes__isnull=False).distinct()
            elif credit_note_status == 'no_credit_notes':
                queryset = queryset.filter(credit_notes__isnull=True)
            elif credit_note_status == 'partially_credited':
                queryset = queryset.filter(
                    credit_notes__isnull=False,
                    payment_status__in=['not_paid', 'partially_paid']
                ).distinct()
        except Exception as e:
            print(f"Error filtering by credit note status: {e}")

        # Due Date Range
        due_date_from = self.request.GET.get('due_date_from')
        due_date_to = self.request.GET.get('due_date_to')
        try:
            if due_date_from:
                queryset = queryset.filter(payment_due_date__gte=due_date_from)
            if due_date_to:
                queryset = queryset.filter(payment_due_date__lte=due_date_to)
        except Exception as e:
            print(f"Error filtering by due date range: {e}")

        # Overdue Filter
        is_overdue = self.request.GET.get('is_overdue')
        try:
            if is_overdue:
                today = timezone.now().date()
                queryset = queryset.filter(
                    payment_due_date__lt=today,
                    payment_status__in=['not_paid', 'partially_paid']
                )
        except Exception as e:
            print(f"Error filtering by overdue invoices: {e}")

        # Print final queryset SQL for debugging
        try:
            print("Final query SQL:", queryset.query)
        except Exception as e:
            print(f"Error printing final query SQL: {e}")

        return queryset.order_by('-date')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter counts
        active_filters = {}
        
        # Date Range
        if self.request.GET.get('date_from') or self.request.GET.get('date_to'):
            date_range = []
            if self.request.GET.get('date_from'):
                date_range.append(f"From: {self.request.GET.get('date_from')}")
            if self.request.GET.get('date_to'):
                date_range.append(f"To: {self.request.GET.get('date_to')}")
            active_filters['date_range'] = ' - '.join(date_range)

        # Supplier
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
                active_filters['supplier'] = supplier.name
            except Supplier.DoesNotExist:
                pass

        # Payment Status
        payment_status = self.request.GET.get('payment_status')
        if payment_status:
            status_display = {
                'not_paid': 'Not Paid',
                'partially_paid': 'Partially Paid',
                'paid': 'Paid'
            }
            active_filters['payment_status'] = status_display.get(payment_status)

        # Amount Range
        if self.request.GET.get('amount_min') or self.request.GET.get('amount_max'):
            amount_range = []
            if self.request.GET.get('amount_min'):
                amount_range.append(f"Min: {self.request.GET.get('amount_min')}")
            if self.request.GET.get('amount_max'):
                amount_range.append(f"Max: {self.request.GET.get('amount_max')}")
            active_filters['amount_range'] = ' - '.join(amount_range)

        # Export Status
        export_status = self.request.GET.get('export_status')
        if export_status:
            active_filters['export_status'] = 'Exported' if export_status == 'exported' else 'Not Exported'

        # Document Type
        document_type = self.request.GET.get('document_type')
        if document_type:
            active_filters['document_type'] = 'Invoice' if document_type == 'invoice' else 'Credit Note'

        context['active_filters'] = active_filters
        context['total_results'] = self.get_queryset().count()
        
        # Add initial supplier data for the filter if selected
        if supplier_id:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
                context['initial_supplier'] = {
                    'id': supplier_id,
                    'text': supplier.name
                }
            except Supplier.DoesNotExist:
                pass

        return context

    def render_to_response(self, context, **response_kwargs):
        """Handle both HTML and AJAX responses"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'html': render_to_string(
                    'invoice/partials/invoice_table.html',
                    context,
                    request=self.request
                ),
                'total_results': context['total_results'],
                'active_filters': context['active_filters']
            })
        return super().render_to_response(context, **response_kwargs)

# Create a new Invoice
class InvoiceCreateView(SuccessMessageMixin, CreateView):
    model = Invoice
    form_class = InvoiceUpdateForm  # Use the custom form here
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully created."

    def form_valid(self, form):
        response = super().form_valid(form)
        # We may want to pass the newly created invoice to the next page or modal
        return response

    def get_form_class(self):
        print("Using CREATE VIEW")  # Debug print
        return InvoiceCreateForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()  # Add all products to the context for dropdown population
        return data

# Update an existing Invoice
class InvoiceUpdateView(SuccessMessageMixin, UpdateView):
    model = Invoice
    form_class = InvoiceUpdateForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully updated."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs) 
        if self.request.POST:
            data['products'] = InvoiceProductInlineFormset(self.request.POST, instance=self.object) 
        else:
             data['products'] = InvoiceProductInlineFormset(instance=self.object, queryset=InvoiceProduct.objects.filter(invoice=self.object))
        return data


    def get_form_class(self):
        print("Using UPDATE VIEW")  # Debug print
        return InvoiceUpdateForm
    
    def form_valid(self, form):
        print("Entering form_valid")
        print("Form data:", form.cleaned_data)
        context = self.get_context_data()
        products = context['products']
        print("Form valid:", form.is_valid())
        print("Products valid:", products.is_valid())
        if not products.is_valid():
            print("Products errors:", products.errors)  # Add this
            print("Non-form errors:", products.non_form_errors())  # And this
        if form.is_valid() and products.is_valid():
            print("Both form and products are valid")
            self.object = form.save()
            products.instance = self.object
            products.save()
            print("Save completed")
            return super().form_valid(form)
        print("Form validation failed")
        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.payment_status == 'paid':
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been paid and cannot be edited!', 
                         extra_tags='danger')
            return redirect('invoice-list')
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be edited!', 
                         extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)

# Delete an Invoice
class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully deleted."

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be deleted!', extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)


InvoiceProductInlineFormset = inlineformset_factory(
    Invoice, InvoiceProduct,
    fields=['product', 'quantity', 'unit_price', 'reduction_rate', 'vat_rate'],
    extra=1,  # Number of empty forms to display
    can_delete=True
)

# Invoice details view for AJAX request
class InvoiceDetailsView(View):
    def get(self, request):
        invoice_id = request.GET.get('invoice_id')
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            products = invoice.products.all()
            product_data = [
                {
                    'name': product.product.name,
                    'unit_price': f"{product.unit_price:,.2f}",
                    'quantity': product.quantity,
                    'vat_rate': f"{product.vat_rate}%",  # Add VAT Rate
                    'reduction_rate': product.reduction_rate,
                    'raw_price': f"{product.quantity * product.unit_price * (1 - product.reduction_rate / 100):,.2f}",
                } for product in products
            ]

            # Calculate total raw amount
            total_raw_amount = sum([
                product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                for product in products
            ])

            # Calculate subtotal per VAT rate
            vat_subtotals = {}
            for product in products:
                vat_rate = product.vat_rate
                raw_price = product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                if vat_rate not in vat_subtotals:
                    vat_subtotals[vat_rate] = 0
                vat_subtotals[vat_rate] += raw_price * (vat_rate / 100)

            response_data = {
                'products': product_data,
                'total_raw_amount': f"{total_raw_amount:,.2f}",  # Add Total Raw Amount
                'vat_subtotals': [{'vat_rate': f"{rate}%", 'subtotal': f"{subtotal:,.2f}"} for rate, subtotal in vat_subtotals.items()],  # Add VAT Subtotals
                'total_vat': f"{invoice.total_tax_amount:,.2f}",
                'total_amount': f"{invoice.total_amount:,.2f}",
            }
            return JsonResponse(response_data)
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'Invoice not found'}, status=404)

# Product Autocomplete View
def product_autocomplete(request):
    query = request.GET.get('term', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(fiscal_label__icontains=query)
    )[:10]
    
    product_list = [{
        "label": f"{product.name} ({product.fiscal_label})",
        "value": product.id
    } for product in products]
    
    if not products:
        product_list.append({
            "label": f"Create new product: {query}",
            "value": "new"
        })
        
    return JsonResponse(product_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class EditProductInInvoiceView(View):
    def get(self, request, pk):
        """
        Handles loading the product data for editing.
        """
        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)
            # Prepare product data to return
            product_data = {
                'product': invoice_product.product.name,
                'product_name': invoice_product.product.name,
                'quantity': invoice_product.quantity,
                'unit_price': float(invoice_product.unit_price),
                'vat_rate': float(invoice_product.vat_rate),
                'reduction_rate': float(invoice_product.reduction_rate),
                'expense_code': invoice_product.product.expense_code,
                'fiscal_label': invoice_product.product.fiscal_label 
            }
            return JsonResponse(product_data, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        """
        Handles updating the product information.
        """
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate')

        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Update the fields with the provided data
            invoice_product.quantity = quantity
            invoice_product.unit_price = unit_price
            invoice_product.vat_rate = vat_rate
            invoice_product.reduction_rate = reduction_rate
            invoice_product.save()

            # Success response
            return JsonResponse({"message": "Product updated successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        """
        Handles deleting the product from the invoice.
        """
        try:
            # Fetch the InvoiceProduct instance
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Delete the instance
            invoice_product.delete()

            # Success response
            return JsonResponse({"message": "Product deleted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportInvoicesView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_export_invoice')

    def generate_excel(self, invoices):
        wb = Workbook()
        ws = wb.active
        ws.title = "Accounting Entries"

        # Define styles
        header_style = {
            'font': Font(bold=True, color='FFFFFF'),
            'fill': PatternFill(start_color='344960', end_color='344960', fill_type='solid'),
            'alignment': Alignment(horizontal='center', vertical='center'),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }

        # Set headers
        headers = ['Date', 'Label', 'Debit', 'Credit', 'Account Code', 'Reference', 'Journal', 'Counterpart']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_style['font']
            cell.fill = header_style['fill']
            cell.alignment = header_style['alignment']
            cell.border = header_style['border']

        # Set column widths
        ws.column_dimensions['A'].width = 12  # Date
        ws.column_dimensions['B'].width = 40  # Label
        ws.column_dimensions['C'].width = 15  # Debit
        ws.column_dimensions['D'].width = 15  # Credit
        ws.column_dimensions['E'].width = 15  # Account Code
        ws.column_dimensions['F'].width = 15  # Reference
        ws.column_dimensions['G'].width = 10  # Journal
        ws.column_dimensions['H'].width = 15  # Counterpart

        current_row = 2
        for invoice in invoices:
            entries = invoice.get_accounting_entries()
            for entry in entries:
                ws.cell(row=current_row, column=1, value=entry['date'].strftime('%d/%m/%Y'))
                ws.cell(row=current_row, column=2, value=entry['label'])
                ws.cell(row=current_row, column=3, value=entry['debit'])
                ws.cell(row=current_row, column=4, value=entry['credit'])
                ws.cell(row=current_row, column=5, value=entry['account_code'])
                ws.cell(row=current_row, column=6, value=entry['reference'])
                ws.cell(row=current_row, column=7, value=entry['journal'])
                ws.cell(row=current_row, column=8, value=entry['counterpart'])

                # Style number cells
                for col in [3, 4]:  # Debit and Credit columns
                    cell = ws.cell(row=current_row, column=col)
                    cell.number_format = '# ##0.00'
                    cell.alignment = Alignment(horizontal='right')

                current_row += 1

        return wb

    def post(self, request):
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            invoices = Invoice.objects.filter(id__in=invoice_ids, exported_at__isnull=True)

            if not invoices:
                return JsonResponse({'error': 'No valid invoices to export'}, status=400)

            # Generate Excel file
            wb = self.generate_excel(invoices)

            # Create export record
            export_record = ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'accounting_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )

            # Mark invoices as exported
            for invoice in invoices:
                invoice.exported_at = timezone.now()
                invoice.export_history.add(export_record)
                invoice.save()

            # Prepare response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{export_record.filename}"'
            wb.save(response)

            return response

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UnexportInvoiceView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_unexport_invoice')

    def post(self, request, invoice_id):
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            if not invoice.exported_at:
                return JsonResponse({'error': 'Invoice is not exported'}, status=400)

            # Create export record for the unexport action
            ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'unexport_{invoice.ref}_{timezone.now().strftime("%Y%m%d_%H%M%S")}',
                note=f'Unexported by {request.user.username}'
            )

            # Clear export date
            invoice.exported_at = None
            invoice.save()

            return JsonResponse({'message': 'Invoice successfully unexported'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class InvoicePaymentDetailsView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        payment_details = invoice.get_payment_details()
        
        # Get all related checks with their details
        checks = Check.objects.filter(cause=invoice).select_related('checker')
        check_details = [{
            'id': str(check.id),
            'reference': f"{getattr(check.checker.bank_account, 'bank', 'Unknown')}-{check.position}",
            'amount': float(check.amount),
            'status': check.status,
            'created_at': check.creation_date.strftime('%Y-%m-%d'),
            'delivered_at': check.delivered_at.strftime('%Y-%m-%d') if check.delivered_at else None,
            'paid_at': check.paid_at.strftime('%Y-%m-%d') if check.paid_at else None,
        } for check in checks]

        return JsonResponse({
            'payment_details': payment_details,
            'checks': check_details
        })

class InvoiceAccountingSummaryView(View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Get original entries
        original_entries = invoice.get_accounting_entries()
        
        # Get credit note entries
        credit_note_entries = []
        credit_notes_total = 0
        for credit_note in invoice.credit_notes.all():
            entries = credit_note.get_accounting_entries()
            credit_note_entries.extend(entries)
            credit_notes_total += credit_note.total_amount
            
        return JsonResponse({
            'original_entries': original_entries,
            'credit_note_entries': credit_note_entries,
            'totals': {
                'original': float(invoice.total_amount),
                'credit_notes': float(-credit_notes_total),
                'net': float(invoice.net_amount)
            }
        })
```

# views_presentation.py

```py

```

# views_product.py

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product
from .forms import ProductForm
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.db import models
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        product = self.get_object()
        print("Current VAT rate:", product.vat_rate)  # Debug print
        print("Form VAT rate:", form.initial.get('vat_rate'))  # Debug print
        return form

    def get_initial(self):
        initial = super().get_initial()
        product = self.get_object()
        print("Initial VAT rate:", product.vat_rate)  # Debug print
        initial['vat_rate'] = product.vat_rate
        return initial

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoiceproduct_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoiceproduct_set.count()} invoice(s).')
            return redirect('product-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete product. It is referenced by one or more invoices.')
            return redirect('product-list')


# AJAX view for creating a new Product
@method_decorator(csrf_exempt, name='dispatch')
class ProductAjaxCreateView(View):
    def post(self, request):
        try:
            name = request.POST.get('name')
            # Check for existing product with same name
            if Product.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'error': f'A product with the name "{name}" already exists.'
                }, status=400)

            product = Product.objects.create(
                name=name,
                fiscal_label=request.POST.get('fiscal_label'),
                is_energy=request.POST.get('is_energy') == 'true',
                expense_code=request.POST.get('expense_code'),
                vat_rate=request.POST.get('vat_rate')
            )
            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(product.id)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailsView(View):
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            return JsonResponse({
                'expense_code': product.expense_code,
                'vat_rate': str(product.vat_rate)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


```

# views_receipts.py

```py
from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import calendar
from .models import CheckReceipt, LCN, CashReceipt, TransferReceipt, BankAccount, Client, Entity
from django.db.models import Q

class ReceiptListView(ListView):
    template_name = 'receipt/receipt_list.html'
    context_object_name = 'receipts'

    def get_queryset(self):
        return {
            'checks': CheckReceipt.objects.select_related('client', 'entity', 'bank_account').all(),
            'lcns': LCN.objects.select_related('client', 'entity', 'bank_account').all(),
            'cash': CashReceipt.objects.select_related('client', 'entity', 'bank_account', 'credited_account').all(),
            'transfers': TransferReceipt.objects.select_related('client', 'entity', 'bank_account', 'credited_account').all()
        }

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptCreateView(View):
    def get(self, request, receipt_type):
        if receipt_type not in ['check', 'lcn', 'cash', 'transfer']:
            return JsonResponse({'error': 'Invalid receipt type'}, status=400)

        # Get current date info
        today = timezone.now()
        current_year = today.year
        current_month = today.month

        # Generate year choices (current year and 2 years back)
        year_choices = range(current_year - 2, current_year + 1)

        # Generate month choices
        month_choices = [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]

        # Get active bank accounts
        bank_accounts = BankAccount.objects.filter(is_active=True)

        context = {
            'receipt_type': receipt_type,
            'title': f'New {receipt_type.title()} Receipt',
            'year_choices': year_choices,
            'month_choices': month_choices,
            'current_year': current_year,
            'current_month': current_month,
            'bank_accounts': bank_accounts
        }

        return render(request, 'receipt/receipt_form_modal.html', context)
    
    def post(self, request, receipt_type):
        try:
            data = request.POST.dict()
            
            # Common fields for all receipt types
            common_fields = {
                'client_id': data['client'],
                'entity_id': data['entity'],
                'operation_date': data['operation_date'],
                'amount': data['amount'],
                'client_year': data['client_year'],
                'client_month': data['client_month'],
                'bank_account_id': data['bank_account'],
                'notes': data.get('notes', '')
            }

            if receipt_type == 'check':
                receipt = CheckReceipt.objects.create(
                    **common_fields,
                    due_date=data['due_date'],
                    check_number=data['check_number'],
                    bank_name=data['bank_name'],
                    branch=data.get('branch', '')
                )
            
            elif receipt_type == 'lcn':
                receipt = LCN.objects.create(
                    **common_fields,
                    due_date=data['due_date'],
                    lcn_number=data['lcn_number'],
                    issuing_bank=data['issuing_bank']
                )
            
            elif receipt_type == 'cash':
                receipt = CashReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    reference_number=data.get('reference_number', '')
                )
            
            elif receipt_type == 'transfer':
                receipt = TransferReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    transfer_reference=data['transfer_reference'],
                    transfer_date=data['transfer_date']
                )
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid receipt type'
                }, status=400)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} created successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptUpdateView(View):
    def get(self, request, receipt_type, pk):
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        try:
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Get current date info for form
            today = timezone.now()
            year_choices = range(today.year - 2, today.year + 1)
            month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
            bank_accounts = BankAccount.objects.filter(is_active=True)

            context = {
                'receipt_type': receipt_type,
                'receipt': receipt,
                'title': f'Edit {receipt_type.title()}',
                'year_choices': year_choices,
                'month_choices': month_choices,
                'bank_accounts': bank_accounts,
                'client': {
                    'id': str(receipt.client.id),
                    'text': f"{receipt.client.name} ({receipt.client.client_code})"
                },
                'entity': {
                    'id': str(receipt.entity.id),
                    'text': f"{receipt.entity.name} ({receipt.entity.ice_code})"
                }
            }

            return render(request, 'receipt/receipt_form_modal.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, receipt_type, pk):
            try:
                data = request.POST.dict()
                model_map = {
                    'check': CheckReceipt,
                    'lcn': LCN,
                    'cash': CashReceipt,
                    'transfer': TransferReceipt
                }
                
                receipt = get_object_or_404(model_map[receipt_type], pk=pk)
                
                # Update common fields
                receipt.client_id = data['client']
                receipt.entity_id = data['entity']
                receipt.operation_date = data['operation_date']
                receipt.amount = data['amount']
                receipt.client_year = data['client_year']
                receipt.client_month = data['client_month']
                receipt.bank_account_id = data['bank_account']
                receipt.notes = data.get('notes', '')

                # Update type-specific fields
                if receipt_type == 'check':
                    receipt.due_date = data['due_date']
                    receipt.check_number = data['check_number']
                    receipt.bank_name = data['bank_name']
                    receipt.branch = data.get('branch', '')
                
                elif receipt_type == 'lcn':
                    receipt.due_date = data['due_date']
                    receipt.lcn_number = data['lcn_number']
                    receipt.issuing_bank = data['issuing_bank']
                
                elif receipt_type == 'cash':
                    receipt.credited_account_id = data['credited_account']
                    receipt.reference_number = data.get('reference_number', '')
                
                elif receipt_type == 'transfer':
                    receipt.credited_account_id = data['credited_account']
                    receipt.transfer_reference = data['transfer_reference']
                    receipt.transfer_date = data['transfer_date']

                receipt.save()

                return JsonResponse({
                    'status': 'success',
                    'message': f'{receipt_type.title()} updated successfully',
                    'id': str(receipt.id)
                })

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDeleteView(View):
    def post(self, request, receipt_type, pk):
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        try:
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            receipt.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ReceiptDetailView(View):
    def get(self, request, receipt_type, pk):
        # Map receipt types to their corresponding models
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        # Get the appropriate model
        model = model_map.get(receipt_type)
        if not model:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid receipt type'
            }, status=400)
        
        # Get the receipt instance
        try:
            receipt = model.objects.select_related(
                'client',
                'entity',
                'bank_account'
            ).get(pk=pk)
            
            # Build context based on receipt type
            context = {
                'receipt': receipt,
                'receipt_type': receipt_type,
                'client': receipt.client,
                'entity': receipt.entity,
                'bank_account': receipt.bank_account,
                'common_fields': {
                    'Operation Date': receipt.operation_date,
                    'Amount': receipt.amount,
                    'Client Year': receipt.client_year,
                    'Client Month': calendar.month_name[receipt.client_month],
                    'Notes': receipt.notes or 'No notes'
                }
            }
            
            # Add type-specific fields
            if receipt_type in ['check', 'lcn']:
                context['specific_fields'] = {
                    'Due Date': receipt.due_date,
                    'Status': receipt.get_status_display() if hasattr(receipt, 'get_status_display') else receipt.status
                }
                if receipt_type == 'check':
                    context['specific_fields'].update({
                        'Check Number': receipt.check_number,
                        'Bank Name': receipt.bank_name,
                        'Branch': receipt.branch or 'N/A'
                    })
                else:  # LCN
                    context['specific_fields'].update({
                        'LCN Number': receipt.lcn_number,
                        'Issuing Bank': receipt.issuing_bank
                    })
            else:  # cash or transfer
                context['specific_fields'] = {
                    'Credited Account': receipt.credited_account.account_number
                }
                if receipt_type == 'cash':
                    context['specific_fields']['Reference Number'] = receipt.reference_number or 'N/A'
                else:  # transfer
                    context['specific_fields'].update({
                        'Transfer Reference': receipt.transfer_reference,
                        'Transfer Date': receipt.transfer_date
                    })
            
            # Render the template
            html = render_to_string('receipt/receipt_detail_modal.html', context)
            return JsonResponse({
                'status': 'success',
                'html': html
            })
            
        except model.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Receipt not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

def client_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    clients = Client.objects.filter(
        Q(name__icontains=search) | 
        Q(client_code__icontains=search)
    )[:10]

    results = [{
        'id': str(client.id),
        'text': f"{client.name} ({client.client_code})"
    } for client in clients]
    print(f"results({len(results)}): {results}")

    return JsonResponse({'results': results})


def entity_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    entities = Entity.objects.filter(
        Q(name__icontains=search) | 
        Q(ice_code__icontains=search)
    )[:10]

    results = [{
        'id': str(entity.id),
        'text': f"{entity.name} ({entity.ice_code})"
    } for entity in entities]
    print(f"results({len(results)}): {results}")
    return JsonResponse({'results': results})
```

# views_supplier.py

```py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Supplier
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = 'supplier/supplier_list.html'
    context_object_name = 'suppliers'

# Create a new Supplier
class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully created."

# Update an existing Supplier
class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully updated."


# Delete a Supplier
class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'supplier/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoice_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoice_set.count()} invoice(s).')
            return redirect('supplier-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete supplier. It is referenced by one or more invoices.')
            return redirect('supplier-list')

```

# views.py

```py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView


# Create your views here.
def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # Redirect to the profile view after successful login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')  # Render the login template

@never_cache
@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def profile(request):
    return render(request, 'profile.html')  # Use 'profile.html' directly


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Welcome, {form.get_user().first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Custom logout view to prevent back button access after logout
@cache_control(no_cache=True, must_revalidate=True)
def logout_view(request):
    logout(request)
    # Redirect to the login page after logout
    response = HttpResponseRedirect('/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
```

