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
    Presentation, PresentationReceipt, MOROCCAN_BANKS)
from django.forms.models import inlineformset_factory
from decimal import Decimal

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
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


logger = logging.getLogger(__name__)

MOROCCAN_BANKS = [
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

    is_current = models.BooleanField(
        default=False,
        help_text="Determines if accounting operations are recorded on this account"
    )
    bank_overdraft = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum allowed overdraft amount"
    )
    overdraft_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Fee applied for overdraft usage"
    )
    has_check_discount_line = models.BooleanField(
        default=False,
        help_text="Indicates if this account can discount checks"
    )
    check_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum amount available for check discounting"
    )
    has_lcn_discount_line = models.BooleanField(
        default=False,
        help_text="Indicates if this account can discount LCNs"
    )
    lcn_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum amount available for LCN discounting"
    )
    stamp_fee_per_receipt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Stamp fee charged per presented receipt"
    )

    def get_available_check_discount_line(self):
        """Calculate remaining check discount line amount"""
        if not self.has_check_discount_line or not self.check_discount_line_amount:
            return Decimal('0.00')
            
        # Get all discounted checks for this account
        total_discounted = PresentationReceipt.objects.filter(
            presentation__bank_account=self,
            presentation__presentation_type='DISCOUNT',
            checkreceipt__isnull=False  # Ensure it's a check
        ).exclude(
            recorded_status__in=['UNPAID', 'PAID'] # Only count currently discounted
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return self.check_discount_line_amount - total_discounted

    def get_available_lcn_discount_line(self):
        """Calculate remaining LCN discount line amount"""
        if not self.has_lcn_discount_line or not self.lcn_discount_line_amount:
            return Decimal('0.00')
            
        discounted_amount = PresentationReceipt.objects.filter(
            presentation__bank_account=self,
            presentation__presentation_type='DISCOUNT',
            lcn__isnull=False,  # Ensure it's an LCN
            lcn__status='DISCOUNTED'  # Only count currently discounted
        ).exclude(
            lcn__status__in=['UNPAID', 'PAID', 'COMPENSATED']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return self.lcn_discount_line_amount - discounted_amount
    
    def get_current_balance(self):
        """Get current balance for the account"""
        from .models import BankStatement  # Import here to avoid circular import
        return BankStatement.calculate_balance_until(self, timezone.now().date())

    def clean(self):
        super().clean()
        if self.has_check_discount_line and not self.check_discount_line_amount:
            raise ValidationError({
                'check_discount_line_amount': 'Amount required when check discount line is enabled'
            })
        if self.has_lcn_discount_line and not self.lcn_discount_line_amount:
            raise ValidationError({
                'lcn_discount_line_amount': 'Amount required when LCN discount line is enabled'
            })

    class Meta:
        ordering = ['bank', 'account_number']


    def __str__(self):
        type_indicator = 'NAT' if self.account_type == 'national' else 'INT'
        return f"{self.bank} [{self.account_number}] - {type_indicator}"

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
    
    def get_transactions(self, year=None, month=None):
        """
        Get all transactions for the client with optional year/month filter.
        For sales: Uses the actual date
        """
        print("\n=== Starting get_transactions ===")
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
                'actual_date': sale.date
            })

        # Calculate previous balance
        if year and month:
            current_date = datetime.date(int(year), int(month), 1)
            previous_balance = 0
            
            print("\n=== Calculating Previous Balance ===")
            
            # Previous Sales (by actual date)
            prev_sales = self.clientsale_set.filter(date__lt=current_date)
            previous_balance = sum(sale.amount for sale in prev_sales)
            print(f"Previous sales balance: {previous_balance}")

            # Previous Checks and LCNs - using the SAME logic as current month
            for receipt_class, type_name in [(CheckReceipt, 'CHECK'), (LCN, 'LCN')]:
                receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('entity')

                print(f"\nProcessing previous {type_name} receipts:")
                for receipt in receipts:
                    print(f"\nReceipt: {type_name} #{receipt.get_receipt_number()}")
                    print(f"Current Status: {receipt.status}")

                    # Get all presentations for this receipt
                    if isinstance(receipt, CheckReceipt):
                        presentations = receipt.check_presentations.select_related('presentation').all()
                    else:
                        presentations = receipt.lcn_presentations.select_related('presentation').all()

                    print(f"Found {presentations.count()} presentations")

                    # Process presentations before current date
                    for pres in presentations:
                            print(f"\nPresentation date: {pres.presentation.date}")
                            number = receipt.check_number if type_name == 'CHECK' else receipt.lcn_number

                            # Add presentation transaction
                            presentation_entry = {
                                'date': pres.presentation.date,
                                'type': type_name,
                                'description': f'{type_name} {number} {receipt.entity.name} presented for '
                                            f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                            f'on {pres.presentation.date.strftime("%Y-%m-%d")}',
                                'debit': None,
                                'credit': receipt.amount,
                                'actual_date': pres.presentation.date
                            }
                            previous_balance -= receipt.amount
                            print(f"Added presentation credit: -{receipt.amount}")

                    # Handle ALL unpaid statuses (history)
                    unpaid_history = ReceiptHistory.objects.filter(
                        content_type=ContentType.objects.get_for_model(receipt_class),
                        object_id=receipt.id,
                        action='status_changed',
                        new_value__status='UNPAID',
                    ).order_by('timestamp')

                    print(f"Found {unpaid_history.count()} unpaid history records")
                    for history in unpaid_history:
                        unpaid_amount = history.new_value.get("amount", receipt.amount)
                        previous_balance += unpaid_amount
                        print(f"Added unpaid debit: +{unpaid_amount}")
                        print(f"From history record: {history.timestamp}")

            # Previous Cash/Transfers (these can't be unpaid)
            for receipt_class, type_name in [(CashReceipt, 'CASH'), (TransferReceipt, 'TRANSFER')]:
                prev_receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('entity')
                total_amount = sum(receipt.amount for receipt in prev_receipts)
                previous_balance -= total_amount
                print(f"\nTotal {type_name} amount: -{total_amount}")

            print(f"\nFinal previous balance: {previous_balance}")

            # Add balance entry even if no transactions in current month
            transactions.insert(0, {
                'date': current_date,
                'type': 'BALANCE',
                'description': 'Previous Balance',
                'debit': max(previous_balance, 0),
                'credit': abs(min(previous_balance, 0)),
                'actual_date': current_date,
                'balance': previous_balance
            })

            # Get current period receipts
            # Handle Checks and LCNs with presentations
            for receipt_class, type_name in [(CheckReceipt, 'CHECK'), (LCN, 'LCN')]:
                receipts = receipt_class.objects.filter(
                    client=self,
                    client_year=year,
                    client_month=month
                ).select_related('entity')

                print(f"\nProcessing {type_name} receipts:")
                for receipt in receipts:
                    print(f"\nReceipt: {type_name} #{receipt.get_receipt_number()}")
                    print(f"Current Status: {receipt.status}")
                    

                    # Get all presentations for this receipt
                    if isinstance(receipt, CheckReceipt):
                        presentations = receipt.check_presentations.select_related('presentation').all()
                    else:
                        presentations = receipt.lcn_presentations.select_related('presentation').all()

                    print(f"Found {presentations.count()} presentations")

                    # Process presentations
                    for pres in presentations:
                        print(f"\nPresentation date: {pres.presentation.date}")
                        number = receipt.check_number if type_name == 'CHECK' else receipt.lcn_number

                        # Determine if this is a representation
                        is_representation = False
                        earlier_presentations = presentations.filter(
                            presentation__date__lt=pres.presentation.date
                        ).exists()
                        if earlier_presentations:
                            is_representation = True

                        # Add presentation transaction
                        presentation_entry = {
                            'date': pres.presentation.date,
                            'type': type_name,
                            'description': f'{type_name} {number} {receipt.entity.name} '
                                        f'({("re" if is_representation else "")}presented for '
                                        f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                        f'on {pres.presentation.date.strftime("%Y-%m-%d")})',
                            'debit': None,
                            'credit': receipt.amount,
                            'actual_date': pres.presentation.date
                        }
                        transactions.append(presentation_entry)
                        print("Added presentation entry:", presentation_entry)

                    # Handle ALL unpaid statuses (history)
                    unpaid_history = ReceiptHistory.objects.filter(
                        content_type=ContentType.objects.get_for_model(receipt_class),
                        object_id=receipt.id,
                        action='status_changed',
                        new_value__status='UNPAID'
                    ).order_by('timestamp')

                    for history in unpaid_history:
                        unpaid_entry = {
                            'date': history.timestamp.date(),
                            'type': f'{type_name}_REVERSAL',
                            'description': f'Reversal of {type_name} {receipt.get_receipt_number()} - '
                                        f'{history.notes if history.notes else "Unpaid"}',
                            'debit': history.new_value.get("amount", receipt.amount),  # Include the unpaid amount
                            'credit': None,
                            'actual_date': history.timestamp.date()
                        }
                        transactions.append(unpaid_entry)
                        print("Added historical unpaid entry:", unpaid_entry)
                # Process current period cash and transfer receipts
        for receipt_class, type_name in [(CashReceipt, 'CASH'), (TransferReceipt, 'TRANSFER')]:
            receipts = receipt_class.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            ).select_related('entity')

            for receipt in receipts:
                transactions.append({
                    'date': receipt.operation_date,
                    'type': type_name,
                    'description': f'{type_name} {receipt.reference_number if hasattr(receipt, "reference_number") else receipt.transfer_reference} {receipt.entity.name}',
                    'debit': None,
                    'credit': receipt.amount,
                    'actual_date': receipt.operation_date
                })

        
        print("\n=== Finished processing transactions ===\n")
        # Sort transactions
        transactions.sort(key=lambda x: (
            x['type'] != 'BALANCE',  # Balance entries first
            x['actual_date'].date() if isinstance(x['actual_date'], datetime.datetime) else x['actual_date']  # Convert datetime to date if needed

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
    STATUS_UNPAID = 'UNPAID'

    RECEIPT_STATUS = [
        (STATUS_PORTFOLIO, 'In Portfolio'),
        (STATUS_PRESENTED_COLLECTION, 'Presented for Collection'),
        (STATUS_PRESENTED_DISCOUNT, 'Presented for Discount'),
        (STATUS_DISCOUNTED, 'Discounted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPENSATED, 'Compensated'),
        (STATUS_UNPAID, 'Unpaid') 
    ]
    
    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('SIGNATURE_MISMATCH', 'Signature Mismatch'),
        ('INVALID_DATE', 'Date Invalid/Post-dated'),
        ('AMOUNT_DISCREPANCY', 'Amount Discrepancy'),
        ('TECHNICAL_ERROR', 'Technical Error (MICR)'),
        ('STOP_PAYMENT', 'Stop Payment Order'),
        ('ACCOUNT_ERROR', 'Account Number Error'),
        ('FORMAL_DEFECT', 'Formal Defect'),
        ('BANK_ERROR', 'Bank Processing Error')
    ]

    bank_account = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    issuing_bank = models.CharField(
        max_length=4,
        choices=MOROCCAN_BANKS
    )

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
    unpaid_date = models.DateTimeField(null=True, blank=True)
    rejection_cause = models.CharField(
        max_length=50,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True
    )    

    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )

    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )
    
    compensation_date = models.DateTimeField(
        null=True,
        blank=True
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

    def get_receipt_number(self):
        """
        Returns the appropriate receipt number based on the receipt type.
        """
        if hasattr(self, 'check_number'):
            return self.check_number
        elif hasattr(self, 'lcn_number'):
            return self.lcn_number
        return ''
    
    def get_presentation_info(self):
        """Returns formatted presentation information if receipt is presented"""
        if self.status in ['PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT','DISCOUNTED', 'PAID', 'REJECTED']:
            presentation_receipt = (
                self.check_presentations.first() if hasattr(self, 'check_presentations') 
                else self.lcn_presentations.first()
            )
            if presentation_receipt and presentation_receipt.presentation:
                pres = presentation_receipt.presentation
                return {
                    'date': pres.date,
                    'ref': f"Presentation #{pres.id}",
                    'bank': pres.bank_account,
                    'type': pres.get_presentation_type_display(),
                    'status': pres.status
                }
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        return not hasattr(self, 'presentation') or self.presentation is None

    def can_delete(self):
        """Check if receipt can be deleted"""
        return self.can_edit()

    def get_status_display_with_details(self):
        """Enhanced status display with presentation details"""
        status_display = self.get_status_display()
        pres_info = self.get_presentation_info()
        
        if pres_info:
            details = (
                f"{pres_info['type']} on {pres_info['date']}\n"
                f"Ref: {pres_info['ref']}\n"
                f"Bank: {pres_info['bank']}"
            )
            return status_display, details
        return status_display, None
    
    @property
    def compensation_info(self):
        """Returns formatted compensation information"""
        if not self.compensating_receipt:
            return None
            
        if isinstance(self.compensating_receipt, CashReceipt):
            return f"Compensated by cash payment (Ref: {self.compensating_receipt.reference_number or 'N/A'})"
        elif isinstance(self.compensating_receipt, TransferReceipt):
            return f"Compensated by bank transfer (Ref: {self.compensating_receipt.transfer_reference})"
        else:
            return (f"Compensated by {self.compensating_receipt.__class__.__name__.replace('Receipt', '')} "
                f"#{self.compensating_receipt.get_receipt_number()} "
                f"({self.compensating_receipt.entity.name})")

    def mark_as_unpaid(self, cause, unpaid_date=None):
        """Mark receipt as unpaid with a cause"""
        if self.status not in ['REJECTED', 'PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT', 'DISCOUNTED']:
            raise ValidationError("Only rejected or presented receipts can be marked as unpaid")
        
        self.status = self.STATUS_UNPAID
        self.rejection_cause = cause
        self.unpaid_date = unpaid_date if unpaid_date else timezone.now()
        self.save()

    def compensate_with(self, compensating_receipt):
        """Set up compensation relationship"""
        if self.status != self.STATUS_UNPAID:
            raise ValidationError("Only unpaid receipts can be compensated")
            
        if compensating_receipt.amount < self.amount:
            raise ValidationError("Compensating receipt amount must be greater than or equal to unpaid amount")

        self.compensating_receipt = compensating_receipt
        
        # If cash/transfer, mark as compensated immediately
        if isinstance(compensating_receipt, (CashReceipt, TransferReceipt)):
            self.status = self.STATUS_COMPENSATED
            self.compensation_date = timezone.now()
            self.record_history(
                action='status_changed',
                old_value={'status': self.STATUS_UNPAID},
                new_value={'status': self.STATUS_COMPENSATED},
                notes=f'Compensated by {compensating_receipt.__class__.__name__} {compensating_receipt.id}'
            )
        else:
            # For checks/LCNs, just record that a compensating receipt was assigned
            self.record_history(
                action='compensation_assigned',
                new_value={
                    'compensating_type': compensating_receipt.__class__.__name__,
                    'compensating_id': str(compensating_receipt.id)
                },
                notes=f'Assigned {compensating_receipt.__class__.__name__} #{compensating_receipt.get_receipt_number()} as compensating receipt'
            )
            
        self.save()

    def handle_compensation_payment(self):
        """Called when a compensating negotiable receipt is paid"""
        if self.status == self.STATUS_UNPAID and self.compensating_receipt:
            old_status = self.status
            self.status = self.STATUS_COMPENSATED
            self.compensation_date = timezone.now()
            
            self.record_history(
                action='status_changed',
                old_value={'status': old_status},
                new_value={'status': self.STATUS_COMPENSATED},
                notes=f'Status changed to compensated as compensating receipt was paid'
            )
            self.save()

    def update_compensated_receipts(self):
            """
            When this receipt is paid, update any receipts it compensates
            """
            # Find all receipts that this receipt compensates
            compensated_checks = CheckReceipt.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id,
                status=self.STATUS_UNPAID
            )
            
            compensated_lcns = LCN.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id,
                status=self.STATUS_UNPAID
            )

            # Update the status of all compensated receipts
            current_time = timezone.now()
            
            for receipt in list(compensated_checks) + list(compensated_lcns):
                receipt.status = self.STATUS_COMPENSATED
                receipt.compensation_date = current_time
                receipt.save()

    def record_history(self, action, old_value=None, new_value=None, notes=None, user=None):
        """
        Record a history event for the negotiable receipt
        """
        content_type = ContentType.objects.get_for_model(self)

        
        
        ReceiptHistory.objects.create(
            content_type=content_type,
            object_id=self.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            user=user
        )

    def delete(self, *args, **kwargs):
        # If this receipt is compensating any unpaid receipts and is still in PORTFOLIO
        if self.status == self.STATUS_PORTFOLIO:
            # Find any receipts this one was supposed to compensate
            compensated_checks = CheckReceipt.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id
            )
            compensated_lcns = LCN.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id
            )
            
            # Clean up the compensated receipts
            for receipt in list(compensated_checks) + list(compensated_lcns):
                receipt.record_history(
                    action='compensation_cancelled',
                    notes=f'Compensating receipt {self.__class__.__name__} #{self.get_receipt_number()} was deleted'
                )
                receipt.compensating_receipt = None
                receipt.save()

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            self.record_history(
                action='created',
                notes=f'Receipt created with status {self.get_status_display()}'
            )
        else:
            try:
                old_instance = type(self).objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    # Check if this is a discount update
                    if self.status == 'DISCOUNTED':
                        # Get the presentation info
                        if hasattr(self, 'check_presentations'):
                            presentation = self.check_presentations.last().presentation
                        else:
                            presentation = self.lcn_presentations.last().presentation
                            
                        self.record_history(
                            action='status_changed',
                            old_value={'status': old_instance.status},
                            new_value={
                                'status': self.status,
                                'presentation_id': str(presentation.id),
                                'bank_account': presentation.bank_account.get_bank_display(),
                                'date': presentation.date.strftime('%Y-%m-%d')
                            },
                            notes=f'Discounted at {presentation.bank_account.get_bank_display()}'
                        )
                    else:
                        self.record_history(
                            action='status_changed',
                            old_value={'status': old_instance.status},
                            new_value={'status': self.status},
                            notes=f'Status changed from {old_instance.status} to {self.status}'
                        )
            except type(self).DoesNotExist:
                pass
                
            super().save(*args, **kwargs)

class CheckReceipt(NegotiableReceipt):
    """Check-specific implementation."""
    check_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Check {self.check_number} - {self.amount}"

    class Meta:
        verbose_name = "Check"
        verbose_name_plural = "Checks"

class LCN(NegotiableReceipt):
    """LCN-specific implementation."""
    lcn_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)

    def can_be_discounted(self):
        """Check if LCN can be discounted based on due date"""
        if not self.due_date:
            return False
            
        days_to_due = (self.due_date - timezone.now().date()).days
        return 20 <= days_to_due <= 120


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

    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )
    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )

    def get_compensated_receipt(self):
        """Returns the receipt that this cash/transfer is compensating"""
        # Check for checks first
        compensated_check = CheckReceipt.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        if compensated_check:
            return compensated_check
            
        # Check for LCNs
        compensated_lcn = LCN.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        return compensated_lcn
    
    def get_compensation_description(self):
        """Returns description if this receipt compensates another"""
        compensated = self.get_compensated_receipt()
        if compensated:
            return f"Compensating unpaid {compensated.__class__.__name__.replace('Receipt', '')} #{compensated.get_receipt_number()}"
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def can_delete(self):
        """Check if receipt can be deleted"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def __str__(self):
        return f"Cash Receipt {self.reference_number or 'N/A'}"

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
    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )
    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )

    def get_compensated_receipt(self):
        """Returns the receipt that this cash/transfer is compensating"""
        # Check for checks first
        compensated_check = CheckReceipt.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        if compensated_check:
            return compensated_check
            
        # Check for LCNs
        compensated_lcn = LCN.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        return compensated_lcn
    
    def get_compensation_description(self):
        """Returns description if this receipt compensates another"""
        compensated = self.get_compensated_receipt()
        if compensated:
            return f"Compensating unpaid {compensated.__class__.__name__.replace('Receipt', '')} #{compensated.get_receipt_number()}"
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def can_delete(self):
        """Check if receipt can be deleted"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def __str__(self):
        return f"Transfer {self.transfer_reference}"

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
    bank_reference = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('presented', 'Presented'),
            ('paid', 'Paid'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    # Optional: Add document field
    document = models.FileField(upload_to='presentations/', null=True, blank=True)

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
    
    recorded_status = models.CharField(
        max_length=20,
        choices=NegotiableReceipt.RECEIPT_STATUS,
        null=True,
        blank=True,
        help_text="Stores the final status decision made in this presentation"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    immutable = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('presentation', 'checkreceipt'),
            ('presentation', 'lcn')
        ]

    def __str__(self):
        receipt = self.checkreceipt or self.lcn
        if receipt:
            return f"Presentation {self.presentation.id} - Receipt {receipt.id}"
        return f"Presentation {self.presentation.id} - No receipt attached"

    def clean(self):
        super().clean()
        if self.checkreceipt and self.lcn:
            raise ValidationError("Cannot have both check and LCN")
        if not self.checkreceipt and not self.lcn:
            raise ValidationError("Must have either check or LCN")
        
        # Get the actual receipt object
        receipt = self.checkreceipt or self.lcn
        
        # Only validate receipt status during initial creation
        if not self.pk:  # If this is a new record
            if getattr(receipt, 'status', None) != 'PORTFOLIO' and getattr(receipt, 'status', None) != 'UNPAID':
                raise ValidationError('Only receipts in portfolio status can be presented')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.presentation.update_total()

        # Update receipt status based on presentation type
        receipt = self.checkreceipt or self.lcn
        if receipt:  # Add check to ensure receipt exists
            if self.presentation.presentation_type == Presentation.TYPE_COLLECTION:
                receipt.status = 'PRESENTED_COLLECTION'
            else:
                receipt.status = 'PRESENTED_DISCOUNT'
            receipt.save()

    class Meta:
        verbose_name = "Presentation Receipt"
        verbose_name_plural = "Presentation Receipts"
        unique_together = [
            ('presentation', 'checkreceipt'),
            ('presentation', 'lcn')
        ]

class ReceiptHistory(BaseModel):
    # Generic Foreign Key to support both Check and LCN receipts
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    receipt = GenericForeignKey('content_type', 'object_id')
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('status_changed', 'Status Changed'),
        ('presented_collection', 'Presented for Collection'),
        ('presented_discount', 'Presented for Discount'),
        ('compensating_assigned', 'Compensating Receipt Assigned'),
        ('compensated', 'Compensated'),
        ('unpaid', 'Marked as Unpaid'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected by Bank')
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    business_date = models.DateTimeField(null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='receipt_history'
    )
    
    class Meta:
        ordering = ['-business_date', '-timestamp']
        verbose_name = "Receipt History"
        verbose_name_plural = "Receipt Histories"

    def record_history(self, action, old_value=None, new_value=None, notes=None, user=None, business_date=None):
        """Record a history event"""
        content_type = ContentType.objects.get_for_model(self)
        
        ReceiptHistory.objects.create(
            content_type=content_type,
            object_id=self.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            user=user,
            business_date=business_date or timezone.now()
        )

    def __str__(self):
        return f"{self.receipt} - {self.action} at {self.timestamp}"

class ClientSale(BaseModel):
    SALE_TYPES = [
        ('BRICKS', 'Bricks'),
        ('TRANSPORT', 'Transport'),
    ]

    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    month = models.IntegerField()
    notes = models.TextField(blank=True)
    sale_type = models.CharField(max_length=10, choices=SALE_TYPES, default='BRICKS')

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.year:
            self.year = self.date.year
        if not self.month:
            self.month = self.date.month
        super().save(*args, **kwargs)


class BankStatement(models.Model):
    """
    Virtual model that dynamically generates bank statement entries.
    Does not store records directly - serves as a view model.
    """
    class Meta:
        managed = False

    def calculate_previous_balance(bank_account, start_date):
        # Start with Jan 1st of current year if start_date is in current year
        # Or Jan 1st of previous year if start_date is in previous year
        year_start = datetime.date(start_date.year, 1, 1)
        
        # Get all entries from year start until start_date
        # (using same logic we use for normal entries but with date range)
        entries = []  # get all entries between year_start and start_date
        
        # Calculate running balance
        balance = Decimal('0.00')  # Assume previous year ended at 0
        for entry in entries:
            balance += (entry.get('credit') or 0) - (entry.get('debit') or 0)
            
        return balance
    
    @classmethod
    def get_statement(cls, bank_account, start_date=None, end_date=None):
        """
        Dynamically generates statement entries for a bank account.
        """
        entries = []
        
        # Get cash receipts
        cash_receipts = CashReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        for receipt in cash_receipts:
            entries.append({
                'date': receipt.operation_date,
                'label': f"Cash payment from {receipt.entity.name}",
                'type': 'CASH',
                'debit': None,
                'credit': receipt.amount,
                'reference': receipt.reference_number or 'N/A',
                'source_type': 'cash_receipt',
                'source_id': receipt.id,
                'can_transfer': True,
                'is_transferred': False
            })
            
        # Get transfer receipts
        transfer_receipts = TransferReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        for receipt in transfer_receipts:
            entries.append({
                'date': receipt.operation_date,
                'label': f"Bank transfer from {receipt.entity.name}",
                'type': 'TRANSFER',
                'debit': None,
                'credit': receipt.amount,
                'reference': receipt.transfer_reference,
                'source_type': 'transfer_receipt',
                'source_id': receipt.id,
                'can_transfer': True,
                'is_transferred': False
            })

        # Get presentations
        presentations = Presentation.objects.filter(
            bank_account=bank_account
        ).prefetch_related(
            'presentation_receipts__checkreceipt',
            'presentation_receipts__lcn'
        )

        for pres in presentations:
            for pr in pres.presentation_receipts.all():
                receipt = pr.checkreceipt or pr.lcn
                receipt_type = 'check' if pr.checkreceipt else 'lcn'
                
                # For collection presentations - only record if marked as PAID
                if pres.presentation_type == 'COLLECTION':
                    if pr.recorded_status == 'PAID':
                        entries.append({
                            'date': pres.date,
                            'label': f"Payment of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}",
                            'type': f'{receipt_type.upper()}_COLLECTION',
                            'debit': None,
                            'credit': receipt.amount,
                            'reference': pres.bank_reference or f"Pres. #{pres.id}",
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'can_transfer': True,
                            'is_transferred': False,
                            'entity': {
                                'name': receipt.entity.name,
                                'ice_code': receipt.entity.ice_code
                            },
                            'client': {
                                'name': receipt.client.name,
                                'client_code': receipt.client.client_code
                            },
                            'due_date': receipt.due_date,
                            'issuing_bank_display': receipt.get_issuing_bank_display(),
                            'presentation_reference': pres.bank_reference,
                            'status': receipt.status if hasattr(receipt, 'status') else None,
                            'rejection_cause': getattr(receipt, 'rejection_cause', None),
                            'rejection_cause_display': receipt.get_rejection_cause_display() if hasattr(receipt, 'get_rejection_cause_display') else None
                        })
                
                # For discount presentations
                elif pres.presentation_type == 'DISCOUNT':
                    # Record initial discount
                    discount_entry = {
                        'date': pres.date,
                        'label': f"Discount of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}",
                        'type': f'{receipt_type.upper()}_DISCOUNT',
                        'debit': None,
                        'credit': receipt.amount,
                        'reference': pres.bank_reference or f"Pres. #{pres.id}",
                        'source_type': 'presentation_receipt',
                        'source_id': pr.id,
                        'can_transfer': True,
                        'is_transferred': False,
                        'entity': {
                            'name': receipt.entity.name,
                            'ice_code': receipt.entity.ice_code
                        },
                        'client': {
                            'name': receipt.client.name,
                            'client_code': receipt.client.client_code
                        },
                        'due_date': receipt.due_date,
                        'issuing_bank_display': receipt.get_issuing_bank_display(),
                        'presentation_reference': pres.bank_reference,
                        'status': receipt.status if hasattr(receipt, 'status') else None,
                        'rejection_cause': getattr(receipt, 'rejection_cause', None),
                        'rejection_cause_display': receipt.get_rejection_cause_display() if hasattr(receipt, 'get_rejection_cause_display') else None
                    }
                    entries.append(discount_entry)

                    # If marked as UNPAID in this presentation
                    if pr.recorded_status == 'UNPAID':
                        # Get unpaid date from history
                        unpaid_history = ReceiptHistory.objects.filter(
                            content_type=ContentType.objects.get_for_model(receipt.__class__),
                            object_id=receipt.id,
                            action='status_changed',
                            new_value__status='UNPAID'
                        ).order_by('timestamp').first()
                        print("Unpaid history:", unpaid_history)
                        print("pres date:", pres.date)
                        unpaid_date = None
                        if unpaid_history:
                            # Convert both to date, ensuring they are always pure dates
                            unpaid_date = (unpaid_history.business_date.date() if unpaid_history.business_date 
                                        else unpaid_history.timestamp.date())
                        else:
                            unpaid_date = pres.date
                        print("Unpaid date:", unpaid_date)
                        print("Type of pres.date:", type(pres.date))
                        print("Type of unpaid_date:", type(unpaid_date))
                    
                        reversal_entry = {
                            'date': unpaid_date,  # Use unpaid date if available
                            'label': (f"Reversal of {receipt_type} "
                                    f"#{receipt.get_receipt_number()} - {receipt.entity.name}"),
                            'type': f'{receipt_type.upper()}_REVERSAL',
                            'debit': receipt.amount,
                            'credit': None,
                            'reference': pres.bank_reference or f"Pres. #{pres.id}",
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,  # Keep original ID
                            'display_id': f"{pr.id}-reversal",  # Add new field for frontend 
                            'can_transfer': False,
                            'is_transferred': False,
                            'discount_reference': discount_entry['reference']  # Link to original discount
                        }
                        entries.append(reversal_entry)

        # Add outgoing transfers
        outgoing_transfers = InterBankTransfer.objects.filter(
            from_bank=bank_account,
            is_deleted=False
        )
        
        for transfer in outgoing_transfers:
            entries.append({
                'date': transfer.date,
                'label': transfer.label,
                'type': 'INTERBANK_TRANSFER_OUT',
                'debit': transfer.total_amount,
                'credit': None,
                'reference': f'Transfer #{transfer.id}',
                'source_type': 'interbank_transfer',
                'source_id': transfer.id,
                'can_delete': True,
                'can_transfer': False,
                'is_transferred': False
            })
            
        # Add incoming transfer records
        incoming_transfers = InterBankTransfer.objects.filter(
            to_bank=bank_account,
            is_deleted=False
        ).prefetch_related('transferred_records')
        
        for transfer in incoming_transfers:
            for record in transfer.transferred_records.all():
                entries.append({
                    'date': transfer.date,
                    'label': f"{transfer.label} - {record.original_label}",
                    'type': 'INTERBANK_TRANSFER_IN',
                    'debit': None,
                    'credit': record.amount,
                    'reference': record.original_reference,
                    'source_type': 'transferred_record',
                    'source_id': record.id,
                    'can_delete': False,
                    'can_transfer': True,
                    'is_transferred': False
                })

        # Check for transferred status
        transferred_records = TransferredRecord.objects.filter(
            source_type__in=[entry['source_type'] for entry in entries],
            source_id__in=[entry['source_id'] for entry in entries]
        ).values_list('source_type', 'source_id')
        
        transferred_set = {(t, i) for t, i in transferred_records}
        
        # Mark transferred entries
        for entry in entries:
            if (entry['source_type'], entry['source_id']) in transferred_set:
                entry['is_transferred'] = True
                entry['can_transfer'] = False

         # Add bank fee transactions
        fee_transactions = BankFeeTransaction.objects.filter(
            bank_account=bank_account
        ).select_related('fee_type', 'related_presentation')

        for fee in fee_transactions:
            entries.append({
                'date': fee.date,
                'label': (f"{fee.fee_type.name}"
                        f"{' - Pres. ' + fee.related_presentation.bank_reference if fee.related_presentation else ''}"),
                'type': 'BANK_FEE',
                'debit': fee.total_amount,
                'credit': None,
                'reference': fee.fee_type.code,
                'source_type': 'bank_fee',
                'source_id': fee.id,
                'can_delete': True,
                'can_transfer': False,
                'is_transferred': False,
                'is_expandable': True,
                'details': {
                    'fee_type': fee.fee_type.name,
                    'raw_amount': fee.raw_amount,
                    'vat_rate': fee.vat_rate,
                    'vat_included': fee.vat_included,
                    'vat_amount': fee.vat_amount,
                    'total_amount': fee.total_amount,
                    'related_presentation': fee.related_presentation.bank_reference if fee.related_presentation else None
                }
        })
            
        initial_balance = Decimal('0.00')
        if start_date:
            # First sort all entries by date
            entries.sort(key=lambda x: x['date'])
            
            # Calculate sum of all operations before start_date
            for entry in entries:
                if entry['date'] < start_date:
                    initial_balance += (entry['credit'] or Decimal('0.00')) - (entry['debit'] or Decimal('0.00'))

            # Add opening balance entry
            entries.append({
                'date': start_date,
                'label': 'Opening Balance',
                'type': 'BALANCE',
                'debit': initial_balance if initial_balance < 0 else None,
                'credit': initial_balance if initial_balance > 0 else None,
                'reference': 'Opening balance',
                'source_type': 'balance',
                'source_id': None,
                'can_transfer': False,
                'is_transferred': False,
                'balance': initial_balance
            })

        # Then your existing date filtering code:
        if start_date or end_date:
            filtered_entries = []
            for entry in entries:
                entry_date = entry['date']
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered_entries.append(entry)
            entries = filtered_entries

        # Your existing sorting:
        entries.sort(key=lambda x: x['date'], reverse=True)
        
        # Replace your existing balance calculation with:
        balance = initial_balance if start_date else Decimal('0.00')
        for entry in reversed(entries):
            if entry['type'] != 'BALANCE':  # Skip balance entry when calculating
                balance += (entry['credit'] or Decimal('0.00')) - (entry['debit'] or Decimal('0.00'))
            entry['balance'] = balance

        return entries
    
    @classmethod
    def calculate_balance_until(cls, bank_account, date):
        """Calculate total balance up to a specific date"""
        entries = cls.get_statement(bank_account, end_date=date)
        if entries:
            return entries[0]['balance']  # First entry has final balance since they're sorted in reverse
        return Decimal('0.00')
        

class AccountingEntry(models.Model):
    """
    Virtual model that dynamically generates accounting entries.
    Does not store records directly - serves as a view model.
    """
    class Meta:
        managed = False

    @classmethod
    def get_entries(cls, bank_account, start_date=None, end_date=None):
        """
        Dynamically generates double-entry accounting records.
        Returns chronologically ordered list of debit/credit pairs.
        """
        entries = []
        
        # Get all relevant receipts and presentations
        cash_receipts = CashReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        transfer_receipts = TransferReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        presentations = Presentation.objects.filter(
            bank_account=bank_account
        ).prefetch_related(
            'presentation_receipts__checkreceipt',
            'presentation_receipts__lcn'
        )
        
        # Process cash receipts
        for receipt in cash_receipts:
            label = f"Cash payment from {receipt.entity.name}"
            reference = receipt.reference_number or 'N/A'
            
            # Add debit and credit pair
            entries.extend([
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': receipt.amount,
                    'credit': None,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': None,
                    'credit': receipt.amount,
                    'account_code': receipt.entity.accounting_code,  # Entity account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                }
            ])
            
        # Process transfer receipts
        for receipt in transfer_receipts:
            label = f"Bank transfer from {receipt.entity.name}"
            reference = receipt.transfer_reference
            
            # Add debit and credit pair
            entries.extend([
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': receipt.amount,
                    'credit': None,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'transfer_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': None,
                    'credit': receipt.amount,
                    'account_code': receipt.entity.accounting_code,  # Entity account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'transfer_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                }
            ])

        # Process presentations
        for pres in presentations:
            for pr in pres.presentation_receipts.all():
                receipt = pr.checkreceipt or pr.lcn
                receipt_type = 'check' if pr.checkreceipt else 'lcn'
                reference = pres.bank_reference or f"Pres. #{pres.id}"
                
                # For collection presentations - only record if marked as PAID
                if pres.presentation_type == 'COLLECTION' and pr.recorded_status == 'PAID':
                    label = f"Payment of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                    
                    # Add debit and credit pair
                    entries.extend([
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': receipt.amount,
                            'credit': None,
                            'account_code': bank_account.accounting_number,  # Bank account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': None,
                            'credit': receipt.amount,
                            'account_code': receipt.entity.accounting_code,  # Entity account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        }
                    ])
                
                # For discount presentations
                elif pres.presentation_type == 'DISCOUNT':
                    # Initial discount entry
                    label = f"Discount of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                    
                    # Add debit and credit pair
                    entries.extend([
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': receipt.amount,
                            'credit': None,
                            'account_code': bank_account.accounting_number,  # Bank account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': None,
                            'credit': receipt.amount,
                            'account_code': '5000',  # On-hold account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        }
                    ])

                    # If marked as unpaid in this presentation, add reversal
                    if pr.recorded_status == 'UNPAID':
                        label = f"Reversal of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                        
                        # Add debit and credit pair for reversal
                        entries.extend([
                            {
                                'date': pres.date,
                                'label': label,
                                'debit': None,
                                'credit': receipt.amount,
                                'account_code': bank_account.accounting_number,  # Bank account
                                'reference': reference,
                                'journal_code': bank_account.journal_number,
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            },
                            {
                                'date': pres.date,
                                'label': label,
                                'debit': receipt.amount,
                                'credit': None,
                                'account_code': '5000',  # On-hold account
                                'reference': reference,
                                'journal_code': bank_account.journal_number,
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            }
                        ])
                        
                    # If paid, record other operations entry
                    elif pr.recorded_status == 'PAID':
                        label = f"Payment of discounted {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                        
                        # Add debit and credit pair for other operations
                        entries.extend([
                            {
                                'date': pres.date,
                                'label': label,
                                'debit': receipt.amount,
                                'credit': None,
                                'account_code': '5000',  # On-hold account
                                'reference': reference,
                                'journal_code': '06',  # Other operations
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            },
                            {
                                'date': pres.date,
                                'label': label,
                                'debit': None,
                                'credit': receipt.amount,
                                'account_code': receipt.entity.accounting_code,  # Entity account
                                'reference': reference,
                                'journal_code': '06',  # Other operations
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            }
                        ])

        incoming_transfers = InterBankTransfer.objects.filter(
            to_bank=bank_account,
            is_deleted=False
        ).prefetch_related('transferred_records')
        
        for transfer in incoming_transfers:
            for transferred_record in transfer.transferred_records.all():
                # Need to get the original record's entity
                if transferred_record.source_type == 'cash_receipt':
                    original_record = CashReceipt.objects.get(id=transferred_record.source_id)
                elif transferred_record.source_type == 'transfer_receipt':
                    original_record = TransferReceipt.objects.get(id=transferred_record.source_id)
                else:  # presentation_receipt
                    pres_receipt = PresentationReceipt.objects.get(id=transferred_record.source_id)
                    original_record = pres_receipt.checkreceipt or pres_receipt.lcn

                # Now we can access the entity
                entries.extend([
                    {
                        'date': transfer.date,
                        'label': f"{transfer.label} - {transferred_record.original_label}",
                        'debit': transferred_record.amount,
                        'credit': None,
                        'account_code': bank_account.accounting_number,  # Bank account
                        'reference': transferred_record.original_reference,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'transferred_record',
                        'source_id': transferred_record.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': transfer.date,
                        'label': f"{transfer.label} - {transferred_record.original_label}",
                        'debit': None,
                        'credit': transferred_record.amount,
                        'account_code': original_record.entity.accounting_code,  # Entity account
                        'reference': transferred_record.original_reference,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'transferred_record',
                        'source_id': transferred_record.id,
                        'pair_index': len(entries) // 2
                    }
                ])
        
        # Bank fee entries
        fee_transactions = BankFeeTransaction.objects.filter(
            bank_account=bank_account
        ).select_related('fee_type')

        for fee in fee_transactions:
            # Raw amount entry
            entries.extend([
                {
                    'date': fee.date,
                    'label': f"{fee.fee_type.name} - Raw Amount",
                    'debit': fee.raw_amount,
                    'credit': None,
                    'account_code': fee.fee_type.accounting_code,  # Fee account
                    'reference': fee.fee_type.code,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'bank_fee',
                    'source_id': fee.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': fee.date,
                    'label': f"{fee.fee_type.name} - Raw Amount",
                    'debit': None,
                    'credit': fee.raw_amount,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': fee.fee_type.code,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'bank_fee',
                    'source_id': fee.id,
                    'pair_index': len(entries) // 2
                }
            ])

            # VAT entry if applicable
            if fee.vat_amount > 0:
                entries.extend([
                    {
                        'date': fee.date,
                        'label': f"{fee.fee_type.name} - VAT",
                        'debit': fee.vat_amount,
                        'credit': None,
                        'account_code': fee.fee_type.vat_code,  # VAT account
                        'reference': fee.fee_type.code,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'bank_fee',
                        'source_id': fee.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': fee.date,
                        'label': f"{fee.fee_type.name} - VAT",
                        'debit': None,
                        'credit': fee.vat_amount,
                        'account_code': bank_account.accounting_number,  # Bank account
                        'reference': fee.fee_type.code,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'bank_fee',
                        'source_id': fee.id,
                        'pair_index': len(entries) // 2
                    }
                ])

        # Filter entries
        if start_date or end_date:
            filtered_entries = []
            for entry in entries:
                entry_date = entry['date']
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered_entries.append(entry)
            entries = filtered_entries

        # Sort entries keeping pairs together
        entries.sort(key=lambda x: (x['date'], x['pair_index']), reverse=True)
        
        return entries

class InterBankTransfer(BaseModel):
    """
    Tracks transfers between bank accounts and their related records.
    """
    from_bank = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        related_name='outgoing_transfers'
    )
    to_bank = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        related_name='incoming_transfers'
    )
    date = models.DateField()
    label = models.CharField(max_length=255, default="Interbank Transfer")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Transfer from {self.from_bank} to {self.to_bank} on {self.date}"

class TransferredRecord(BaseModel):
    """
    Links original statement records to their transfer.
    """
    transfer = models.ForeignKey(
        InterBankTransfer, 
        on_delete=models.CASCADE,
        related_name='transferred_records'
    )
    # Source type and id for the original record
    source_type = models.CharField(max_length=50)  # 'cash_receipt', 'transfer_receipt', 'presentation_receipt'
    source_id = models.UUIDField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    original_date = models.DateField()
    original_label = models.CharField(max_length=255)
    original_reference = models.CharField(max_length=100)

    class Meta:
        unique_together = ['source_type', 'source_id']  # Prevent double transfers

    def __str__(self):
        return f"Transferred record {self.source_type}:{self.source_id}"
    
class BankFeeType(BaseModel):
    """Defines bank fee types and their accounting codes"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)  # For reference/initials
    accounting_code = models.CharField(max_length=5)  # Fee account code
    vat_code = models.CharField(max_length=5)  # VAT account code
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class BankFeeTransaction(BaseModel):
    """Records bank fee transactions"""
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    fee_type = models.ForeignKey(BankFeeType, on_delete=models.PROTECT)
    date = models.DateField()
    related_presentation = models.ForeignKey(
        'Presentation', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    raw_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=10.00,
        null=True,
        blank=True
    )
    vat_included = models.BooleanField(default=False)
    vat_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)

    def calculate_amounts(self):
        """Calculate VAT and total amounts based on settings"""
        if not self.vat_rate or self.vat_rate == 0:
            self.vat_amount = Decimal('0.00')
            self.total_amount = self.raw_amount
        elif self.vat_included:
            # If VAT included, calculate backwards
            vat_multiplier = (self.vat_rate / 100) + 1
            self.raw_amount = self.total_amount / vat_multiplier
            self.vat_amount = self.total_amount - self.raw_amount
        else:
            # Calculate VAT and total from raw amount
            self.vat_amount = self.raw_amount * (self.vat_rate / 100)
            self.total_amount = self.raw_amount + self.vat_amount

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.calculate_amounts()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fee_type.name} - {self.date}"

# Add initial fee types
INITIAL_FEE_TYPES = [
    {
        'name': 'Account Management Fee',
        'code': 'AMF',
        'accounting_code': '61411',
        'vat_code': '34551'
    },
    {
        'name': 'Statement Fee',
        'code': 'STF',
        'accounting_code': '61412',
        'vat_code': '34551'
    },
    {
        'name': 'Check Processing Fee',
        'code': 'CPF',
        'accounting_code': '61413',
        'vat_code': '34551'
    },
    {
        'name': 'Transfer Commission',
        'code': 'TRC',
        'accounting_code': '61414',
        'vat_code': '34551'
    },
    {
        'name': 'Check Book Fee',
        'code': 'CBF',
        'accounting_code': '61415',
        'vat_code': '34551'
    },
    {
        'name': 'Payment Rejection Fee',
        'code': 'PRF',
        'accounting_code': '61416',
        'vat_code': '34551'
    },
    {
        'name': 'Check Discount Commission',
        'code': 'CDC',
        'accounting_code': '61417',
        'vat_code': '34551'
    },
    {
        'name': 'LCN Discount Commission',
        'code': 'LDC',
        'accounting_code': '61418',
        'vat_code': '34551'
    }
]

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

# templates/bank/accounting.html

```html
{% extends 'base.html' %} {% load accounting_filters %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ bank_account.bank }} - {{ bank_account.account_number }} Accounting</h2> <div class="d-flex gap-2"> <!-- Filter Form --> <form class="form-inline" id="accountingFilterForm"> <div class="input-group"> <input type="date" class="form-control" name="start_date" id="startDate"> <input type="date" class="form-control" name="end_date" id="endDate"> <button type="submit" class="btn btn-primary">Apply</button> </div> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-6"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Debit</h5> <p class="card-text text-danger h4">{{ total_debit|format_balance }}</p> </div> </div> </div> <div class="col-md-6"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Credit</h5> <p class="card-text text-success h4">{{ total_credit|format_balance }}</p> </div> </div> </div> </div> <!-- Accounting Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Label</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th>Account Code</th> <th>Reference</th> <th>Journal Code</th> <th>Actions</th> </tr> </thead> <tbody id="accountingTableBody"> {% include 'bank/partials/accounting_table.html' %} </tbody> </table> </div> </div> <script> $(document).ready(function() { // Existing filter form handler with validation $('#accountingFilterForm').on('submit', function(e) { e.preventDefault(); const startDate = this.querySelector('[name="start_date"]').value; const endDate = this.querySelector('[name="end_date"]').value; if (!validateDateRange(startDate, endDate)) { showToast('Start date must be before or equal to end date', 'error'); return; } $.get(window.location.pathname, $(this).serialize()) .done(function(response) { $('#accountingTableBody').html(response.html); }) .fail(function(xhr) { showToast('Error loading accounting data', 'error'); }); }); // Add helper functions function validateDateRange(startDate, endDate) { if (!startDate || !endDate) return true; return new Date(startDate) <= new Date(endDate); } function showToast(message, type = 'error') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } }); // View functions function viewReceipt(type, id) { $.get(`/testapp/receipts/details/${type}/${id}/`) .done(function(response) { $('#receiptDetailModal .modal-content').html(response.html); $('#receiptDetailModal').modal('show'); }) .fail(function(xhr) { showToast('Error loading receipt details', 'error'); }); } function viewPresentation(id) { $.get(`/testapp/presentations/${id}/`) .done(function(response) { $('#presentationDetailModal .modal-content').html(response); $('#presentationDetailModal').modal('show'); }) .fail(function(xhr) { showToast('Error loading presentation details', 'error'); }); } </script> {% endblock %}
```

# templates/bank/bank_list.html

```html
{% extends 'base.html' %} {% load accounting_filters %} {% block content %} <div class="container-fluid px-4"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Bank Accounts</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#bankAccountModal"> <i class="fas fa-plus"></i> New Bank Account </button> </div> <!-- Accounts Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Bank</th> <th>Account Number</th> <th>Type</th> <th>City</th> <th>Status</th> <th>Current Account</th> <th>Check Discount</th> <th>LCN Discount</th> <th class="text-right">Balance</th> <th>Actions</th> </tr> </thead> <tbody> <tbody> {% for account in accounts %} <tr> <td>{{ account.get_bank_display }}</td> <td>{{ account.account_number }}</td> <td>{{ account.get_account_type_display }}</td> <td>{{ account.city }}</td> <td> <span class="badge {% if account.is_active %}badge-success{% else %}badge-danger{% endif %}"> {{ account.is_active|yesno:"Active,Inactive" }} </span> </td> <td> <span class="badge {% if account.is_current %}badge-primary{% else %}badge-secondary{% endif %}"> {{ account.is_current|yesno:"Yes,No" }} </span> </td> <td> {% if account.has_check_discount_line %} <span class="badge badge-info discount-info" data-toggle="popover" data-trigger="hover" data-html="true" data-title="Check Discount Details" data-content=" <strong>Total Line:</strong> {{ account.check_discount_line_amount|format_balance }}<br> <strong>Used Amount:</strong> {{ account.check_discount_line_amount|sub:account.get_available_check_discount_line|format_balance }}<br> <strong>Available:</strong> {{ account.get_available_check_discount_line|format_balance }} "> {{ account.check_discount_line_amount|format_balance }} MAD </span> {% else %} <span class="badge badge-secondary">No</span> {% endif %} </td> <td> {% if account.has_lcn_discount_line %} <span class="badge badge-info discount-info" data-toggle="popover" data-trigger="hover" data-html="true" data-title="LCN Discount Details" data-content=" <strong>Total Line:</strong> {{ account.lcn_discount_line_amount|format_balance }}<br> <strong>Used Amount:</strong> {{ account.lcn_discount_line_amount|sub:account.get_available_lcn_discount_line|format_balance }}<br> <strong>Available:</strong> {{ account.get_available_lcn_discount_line|format_balance }} "> {{ account.lcn_discount_line_amount|format_balance }} MAD </span> {% else %} <span class="badge badge-secondary">No</span> {% endif %} </td> <td class="text-right"> <span class="{% if account.current_balance < 0 %}text-danger{% else %}text-success{% endif %}"> {{ account.current_balance|format_balance }} </span> </td> <td> <div class="btn-group"> <a href="{% url 'bank-statement' account.id %}" class="btn btn-sm btn-info" title="View Statement"> <i class="fas fa-file-alt"></i> </a> <a href="{% url 'bank-accounting' account.id %}" class="btn btn-sm btn-secondary" title="View Accounting"> <i class="fas fa-book"></i> </a> <a href="{% url 'other-operations' account.id %}" class="btn btn-sm btn-warning" title="Other Operations"> <i class="fas fa-exchange-alt"></i> </a> <button class="btn btn-sm btn-primary" onclick="editBankAccount('{{ account.id }}')" title="Edit"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger" onclick="deleteBankAccount('{{ account.id }}')" title="Delete"> <i class="fas fa-trash"></i> </button> </div> </td> <td style="display:none"> Check line: {{ account.get_available_check_discount_line }} LCN line: {{ account.get_available_lcn_discount_line }} Raw check amount: {{ account.check_discount_line_amount }} Raw lcn amount: {{ account.lcn_discount_line_amount }} </td> </tr> {% empty %} <tr> <td colspan="9" class="text-center">No bank accounts found</td> </tr> {% endfor %} </tbody> </table> </div> </div> </div> </div> <!-- Bank Account Modal --> <div class="modal fade" id="bankAccountModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title" id="modalTitle">New Bank Account</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="bankAccountForm"> {% csrf_token %} <input type="hidden" id="accountId"> <!-- Basic Information --> <div class="card mb-3"> <div class="card-header"> Basic Information </div> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Bank</label> <select class="form-control" id="bank" required> {% for code, name in bank_choices %} <option value="{{ code }}">{{ name }}</option> {% endfor %} </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Account Number</label> <input type="text" class="form-control" id="accountNumber" required> </div> </div> </div> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label>Accounting Number</label> <input type="text" class="form-control" id="accountingNumber" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Journal Number</label> <input type="text" class="form-control" id="journalNumber" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>City</label> <input type="text" class="form-control" id="city" required> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Account Type</label> <select class="form-control" id="accountType" required> <option value="national">National</option> <option value="international">International</option> </select> </div> </div> <div class="col-md-6"> <div class="form-check mt-4"> <input type="checkbox" class="form-check-input" id="isActive" checked> <label class="form-check-label">Active Account</label> </div> <div class="form-check"> <input type="checkbox" class="form-check-input" id="isCurrent"> <label class="form-check-label">Current Account</label> </div> </div> </div> </div> </div> <!-- Financial Parameters --> <div class="card mb-3"> <div class="card-header"> Financial Parameters </div> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Bank Overdraft</label> <input type="number" class="form-control" id="bankOverdraft" step="0.01" min="0"> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Overdraft Fee (%)</label> <input type="number" class="form-control" id="overdraftFee" step="0.01" min="0"> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-check mb-2"> <input type="checkbox" class="form-check-input" id="hasCheckDiscountLine"> <label class="form-check-label">Has Check Discount Line</label> </div> <div class="form-group check-discount-amount d-none"> <label>Check Discount Line Amount</label> <input type="number" class="form-control" id="checkDiscountLineAmount" step="0.01" min="0"> </div> </div> <div class="col-md-6"> <div class="form-check mb-2"> <input type="checkbox" class="form-check-input" id="hasLcnDiscountLine"> <label class="form-check-label">Has LCN Discount Line</label> </div> <div class="form-group lcn-discount-amount d-none"> <label>LCN Discount Line Amount</label> <input type="number" class="form-control" id="lcnDiscountLineAmount" step="0.01" min="0"> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Stamp Fee per Receipt</label> <input type="number" class="form-control" id="stampFeePerReceipt" step="0.01" min="0"> </div> </div> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveBankAccount">Save</button> </div> </div> </div> </div> {% endblock %} <style> .popover { max-width: 300px; } .popover-body { padding: 1rem; line-height: 1.5; } .discount-info { cursor: pointer; } /* Ensure popovers appear above other elements */ .popover { z-index: 1060; } </style> {% block extra_js %} <script> const BankAccountManager = { init() { this.bindEvents(); this.setupValidation(); }, bindEvents() { $('#saveBankAccount').on('click', () => this.saveBankAccount()); // Toggle discount line amount inputs $('#hasCheckDiscountLine').change(function() { $('.check-discount-amount').toggleClass('d-none', !this.checked); if (this.checked) { $('#checkDiscountLineAmount').prop('required', true); } else { $('#checkDiscountLineAmount').prop('required', false).val(''); } }); $('#hasLcnDiscountLine').change(function() { $('.lcn-discount-amount').toggleClass('d-none', !this.checked); if (this.checked) { $('#lcnDiscountLineAmount').prop('required', true); } else { $('#lcnDiscountLineAmount').prop('required', false).val(''); } }); // Reset form on modal close $('#bankAccountModal').on('hidden.bs.modal', () => { this.resetForm(); }); }, setupValidation() { const form = document.getElementById('bankAccountForm'); // Add validation for numeric fields ['bankOverdraft', 'overdraftFee', 'checkDiscountLineAmount', 'lcnDiscountLineAmount', 'stampFeePerReceipt'].forEach(id => { const input = document.getElementById(id); input.addEventListener('input', () => { const value = parseFloat(input.value); if (value < 0) { input.setCustomValidity('Value must be positive'); } else { input.setCustomValidity(''); } }); }); }, async saveBankAccount() { const form = document.getElementById('bankAccountForm'); if (!form.checkValidity()) { form.reportValidity(); return; } const data = { bank: $('#bank').val(), account_number: $('#accountNumber').val(), accounting_number: $('#accountingNumber').val(), journal_number: $('#journalNumber').val(), city: $('#city').val(), account_type: $('#accountType').val(), is_active: $('#isActive').prop('checked'), is_current: $('#isCurrent').prop('checked'), bank_overdraft: $('#bankOverdraft').val() || null, overdraft_fee: $('#overdraftFee').val() || null, has_check_discount_line: $('#hasCheckDiscountLine').prop('checked'), check_discount_line_amount: $('#hasCheckDiscountLine').prop('checked') ? $('#checkDiscountLineAmount').val() : null, has_lcn_discount_line: $('#hasLcnDiscountLine').prop('checked'), lcn_discount_line_amount: $('#hasLcnDiscountLine').prop('checked') ? $('#lcnDiscountLineAmount').val() : null, stamp_fee_per_receipt: $('#stampFeePerReceipt').val() || null }; const id = $('#accountId').val(); const url = id ? `/testapp/bank-accounts/${id}/edit/` : '/testapp/bank-accounts/create/'; const method = id ? 'POST' : 'POST'; try { const response = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const result = await response.json(); if (response.ok) { $('#bankAccountModal').modal('hide'); showToast('Success', result.message); location.reload(); } else { showToast('Error', result.message); } } catch (error) { showToast('Error', 'Failed to save bank account'); console.error('Error:', error); } }, resetForm() { const form = document.getElementById('bankAccountForm'); form.reset(); $('#accountId').val(''); $('#modalTitle').text('New Bank Account'); $('.check-discount-amount, .lcn-discount-amount').addClass('d-none'); $('#checkDiscountLineAmount, #lcnDiscountLineAmount').prop('required', false); } }; // Initialize when document is ready $(document).ready(function() { BankAccountManager.init(); // Initialize popovers $('[data-toggle="popover"]').popover({ container: 'body', boundary: 'window' }); // Destroy popover when mouse leaves $('.discount-info').on('mouseleave', function() { $(this).popover('hide'); }); }); // Global functions for edit and delete function editBankAccount(id) { fetch(`/testapp/bank-accounts/${id}/edit/`) .then(response => response.json()) .then(data => { $('#accountId').val(id); $('#modalTitle').text('Edit Bank Account'); // Fill in the form $('#bank').val(data.bank); $('#accountNumber').val(data.account_number); $('#accountingNumber').val(data.accounting_number); $('#journalNumber').val(data.journal_number); $('#city').val(data.city); $('#accountType').val(data.account_type); $('#isActive').prop('checked', data.is_active); $('#isCurrent').prop('checked', data.is_current); $('#bankOverdraft').val(data.bank_overdraft); $('#overdraftFee').val(data.overdraft_fee); $('#hasCheckDiscountLine').prop('checked', data.has_check_discount_line).trigger('change'); $('#checkDiscountLineAmount').val(data.check_discount_line_amount); $('#hasLcnDiscountLine').prop('checked', data.has_lcn_discount_line).trigger('change'); $('#lcnDiscountLineAmount').val(data.lcn_discount_line_amount); $('#stampFeePerReceipt').val(data.stamp_fee_per_receipt); $('#bankAccountModal').modal('show'); }) .catch(error => { showToast('Error', 'Failed to load bank account details'); console.error('Error:', error); }); } function deleteBankAccount(id) { if (!confirm('Are you sure you want to delete this bank account?')) { return; } fetch(`/testapp/bank-accounts/${id}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }) .then(response => response.json()) .then(result => { if (result.status === 'success') { showToast('Success', result.message); location.reload(); } else { showToast('Error', result.message); } }) .catch(error => { showToast('Error', 'Failed to delete bank account'); console.error('Error:', error); }); } function showToast(title, message) { // Implementation remains the same as before } </script> {% endblock %}
```

# templates/bank/bank_statement.html

```html
{% extends 'base.html' %} {% load accounting_filters %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ bank_account.bank }} - {{ bank_account.account_number }} Statement</h2> <div class="d-flex gap-2"> <!-- Transfer Button --> <button id="transferBtn" class="btn btn-primary" disabled> <i class="fas fa-exchange-alt me-2"></i> Transfer Selected </button> <!-- Add button to header section --> <button class="btn btn-info ms-2" id="addBankFee"> <i class="fas fa-coins me-2"></i> Add Bank Fee </button> <!-- Filter Form --> <form class="form-inline" id="statementFilterForm"> <div class="input-group"> <input type="date" class="form-control" name="start_date" id="startDate"> <input type="date" class="form-control" name="end_date" id="endDate"> <button type="submit" class="btn btn-primary">Apply</button> </div> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Debit</h5> <p class="card-text text-danger h4" id="total-debit">{{ total_debit|format_balance }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Credit</h5> <p class="card-text text-success h4" id="total-credit">{{ total_credit|format_balance }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Balance</h5> <p class="card-text h4 {% if final_balance > 0 %}text-success{% else %}text-danger{% endif %}" id="final-balance"> {{ final_balance|format_balance }} </p> </div> </div> </div> </div> <!-- Statement Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th style="width: 40px;"> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="selectAll"> <label class="custom-control-label" for="selectAll"></label> </div> </th> <th>Date</th> <th>Label</th> <th>Type</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th>Reference</th> <th class="text-right">Balance</th> <th>Actions</th> </tr> </thead> <tbody id="statementTableBody"> {% for entry in entries %} <tr class="record-row" data-record-id="{{ entry.display_id|default:entry.source_id }}" data-type="{{ entry.type|lower }}"> <td> {% if entry.can_transfer %} <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input record-checkbox" id="record{{ entry.source_id }}" data-amount="{{ entry.credit }}" data-source-type="{{ entry.source_type }}" data-source-id="{{ entry.source_id }}" data-date="{{ entry.date|date:'Y-m-d' }}" data-label="{{ entry.label }}" data-reference="{{ entry.reference }}"> <label class="custom-control-label" for="record{{ entry.source_id }}"></label> </div> {% endif %} {% if entry.is_transferred %} <span class="badge badge-info" title="Transferred"> <i class="fas fa-exchange-alt"></i> </span> {% endif %} </td> <td>{{ entry.date|date:"Y-m-d" }}</td> <td>{{ entry.label }}</td> <td> <span class="badge badge-{{ entry.type|lower }}">{{ entry.type }}</span> </td> <td class="text-right text-danger"> {% if entry.debit %}{{ entry.debit|format_balance }}{% endif %} </td> <td class="text-right text-success"> {% if entry.credit %}{{ entry.credit|format_balance }}{% endif %} </td> <td>{{ entry.reference }}</td> <td class="text-right {% if entry.balance > 0 %}text-success{% else %}text-danger{% endif %}"> {{ entry.balance|format_balance }} </td> <td> <!-- Add the toggle button for details --> <button class="btn btn-sm btn-link toggle-details" title="Show Details"> <i class="fas fa-chevron-down"></i> </button> <!-- Existing action buttons --> <div class="btn-group"> {% if entry.can_delete %} {% if entry.type == 'BANK_FEE' %} <button class="btn btn-sm btn-danger" onclick="deleteBankFee('{{ entry.source_id }}')"> <i class="fas fa-trash"></i> </button> {% else %} <button class="btn btn-sm btn-danger" onclick="deleteTransfer('{{ entry.source_id }}')"> <i class="fas fa-trash"></i> </button> {% endif %} {% endif %} </div> </td> </tr> <!-- The details row --> <tr class="details-row d-none" data-record-id="{{ entry.display_id|default:entry.source_id }}"> <td colspan="9"> <div class="card"> <div class="card-body"> {% if entry.type == 'BANK_FEE' %} <!-- Existing bank fee details here --> <div class="row"> <div class="col-md-3"> <strong>Fee Type:</strong><br> {{ entry.details.fee_type }} </div> <div class="col-md-3"> <strong>Raw Amount:</strong><br> {{ entry.details.raw_amount|format_balance }} </div> <div class="col-md-3"> <strong>VAT Rate:</strong><br> {{ entry.details.vat_rate }}% </div> <div class="col-md-3"> <strong>VAT Included:</strong><br> {{ entry.details.vat_included|yesno:"Yes,No" }} </div> </div> <div class="row mt-3"> <div class="col-md-4"> <strong>VAT Amount:</strong><br> {{ entry.details.vat_amount|format_balance }} </div> <div class="col-md-4"> <strong>Total Amount:</strong><br> {{ entry.details.total_amount|format_balance }} </div> <div class="col-md-4"> <strong>Related Presentation:</strong><br> {{ entry.details.related_presentation|default:"None" }} </div> </div> {% elif entry.type == 'CASH' %} <div class="row"> <div class="col-md-3"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-3"> <strong>Client:</strong><br> {{ entry.client_name }} </div> <div class="col-md-3"> <strong>Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-3"> <strong>Operation Date:</strong><br> {{ entry.operation_date|date:"Y-m-d" }} </div> </div> {% elif entry.type == 'TRANSFER' %} <div class="row"> <div class="col-md-4"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-4"> <strong>Transfer Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-4"> <strong>Transfer Date:</strong><br> {{ entry.transfer_date|date:"Y-m-d" }} </div> </div> {% elif 'CHECK' in entry.type or 'LCN' in entry.type %} <div class="row"> <div class="col-md-6"> <div class="mb-3"> <strong>Entity:</strong><br> {{ entry.entity.name }} ({{ entry.entity.ice_code }}) </div> <div class="mb-3"> <strong>Client:</strong><br> {{ entry.client.name }} ({{ entry.client.client_code }}) </div> <div class="mb-3"> <strong>Due Date:</strong><br> {{ entry.due_date|date:"Y-m-d" }} </div> </div> <div class="col-md-6"> <div class="mb-3"> <strong>Issuing Bank:</strong><br> {{ entry.issuing_bank_display }} </div> <div class="mb-3"> <strong>Operation Details:</strong><br> {% if entry.type == 'CHECK_DISCOUNT' or entry.type == 'LCN_DISCOUNT' %} Discount Date: {{ entry.date|date:"Y-m-d" }}<br> {% if entry.presentation_reference %} Presentation: {{ entry.presentation_reference }} {% endif %} {% elif entry.type == 'CHECK_COLLECTION' or entry.type == 'LCN_COLLECTION' %} Collection Date: {{ entry.date|date:"Y-m-d" }}<br> {% if entry.presentation_reference %} Presentation: {{ entry.presentation_reference }} {% endif %} {% endif %} </div> {% if entry.status %} <div class="mb-3"> <strong>Status:</strong><br> <span class="badge badge-{{ entry.status|lower }}"> {{ entry.status }} </span> {% if entry.rejection_cause %} <br><small class="text-danger">{{ entry.rejection_cause_display }}</small> {% endif %} </div> {% endif %} </div> </div> {% endif %} </div> </div> </td> </tr> {% empty %} <tr> <td colspan="9" class="text-center">No entries found for this period</td> </tr> {% endfor %} </tbody> <!-- Transfer Modal --> <div class="modal fade" id="transferModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <i class="fas fa-exchange-alt me-2"></i> Create Interbank Transfer </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="transferForm"> {% csrf_token %} <!-- Transfer Details --> <div class="card mb-3"> <div class="card-body"> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label>Transfer To</label> <select class="form-control" id="toBankAccount" required> <option value="">Select Bank Account</option> {% for account in bank_accounts %} {% if account.id != bank_account.id %} <option value="{{ account.id }}"> {{ account.bank }} - {{ account.account_number }} </option> {% endif %} {% endfor %} </select> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Transfer Date</label> <input type="date" class="form-control" id="transferDate" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Label</label> <input type="text" class="form-control" id="transferLabel" value="Interbank Transfer"> </div> </div> </div> </div> </div> <!-- Selected Records --> <div class="card"> <div class="card-header d-flex justify-content-between align-items-center"> <h6 class="mb-0">Selected Records</h6> <span class="text-primary"> Total: <strong id="selectedTotal">0.00</strong> MAD </span> </div> <div class="card-body"> <div id="selectedRecordsList" class="list-group list-group-flush"> <!-- Will be populated by JavaScript --> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveTransfer"> <i class="fas fa-save me-2"></i> Create Transfer </button> </div> </div> </div> </div> <!-- Bank Fee Modal --> <div class="modal fade" id="bankFeeModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <i class="fas fa-coins me-2"></i> Record Bank Fee </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="bankFeeForm"> {% csrf_token %} <!-- Fee Details --> <div class="card mb-3"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Fee Type</label> <select class="form-control" id="feeType" required> <option value="">Select Fee Type</option> {% for fee_type in fee_types %} <option value="{{ fee_type.id }}"> {{ fee_type.name }} </option> {% endfor %} </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Date</label> <input type="date" class="form-control" id="feeDate" required> </div> </div> </div> <div class="form-group mt-3"> <label>Related Presentation</label> <input type="text" class="form-control" id="relatedPresentation" placeholder="Search by reference..."> </div> </div> </div> <!-- Amount Details --> <div class="card"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Fee Amount</label> <input type="number" class="form-control" id="rawAmount" step="0.01" min="0.01" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>VAT Rate (%)</label> <select class="form-control" id="vatRate"> <option value="">No VAT</option> <option value="20">20%</option> <option value="16">16%</option> <option value="11">11%</option> <option value="10" selected>10%</option> <option value="7">7%</option> <option value="0">0%</option> </select> </div> </div> </div> <div class="form-check mt-3"> <input type="checkbox" class="form-check-input" id="vatIncluded"> <label class="form-check-label" for="vatIncluded"> VAT Included in Amount </label> </div> <div class="row mt-3"> <div class="col-md-6"> <div class="form-group"> <label>VAT Amount</label> <input type="number" class="form-control" id="vatAmount" step="0.01" min="0" readonly> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Total Amount</label> <input type="number" class="form-control" id="totalAmount" step="0.01" min="0.01" readonly> </div> </div> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveBankFee"> <i class="fas fa-save me-2"></i> Record Fee </button> </div> </div> </div> </div> {% endblock %} <style> .record-row { cursor: pointer; } .record-row:hover { background-color: rgba(0,0,0,.02); } .toggle-details { padding: 0; transition: transform 0.2s; } .toggle-details:focus { outline: none; box-shadow: none; } .details-row { background-color: #f8f9fa; } .details-row .card { border: none; margin: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); } .details-row strong { color: #6c757d; font-size: 0.875rem; } /* Fee Row Styling */ .fee-row { cursor: pointer; transition: background-color 0.2s; } .fee-row:hover { background-color: rgba(0, 0, 0, 0.02); } .fee-row .toggle-fee-details { padding: 0; margin-left: 8px; color: #6c757d; transition: transform 0.3s; } /* Details Row Styling */ .fee-details-row { background-color: #f8f9fa; transition: all 0.3s ease; overflow: hidden; } .fee-details-row .card { border: none; margin: 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); } .fee-details-row .card-body { padding: 1.5rem; } .fee-details-row strong { color: #6c757d; font-size: 0.875rem; } /* Button Spacing & Styling */ .btn-group { gap: 0.5rem; } .btn-group > .btn { border-radius: 0.375rem !important; margin: 0; } /* Modal Enhancements */ .modal-content { border: none; border-radius: 0.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.1); } .modal-header { background: linear-gradient(45deg, #4e73df, #224abe); color: white; border-top-left-radius: 0.5rem; border-top-right-radius: 0.5rem; padding: 1.5rem; } .modal-body { padding: 1.5rem; } .modal-footer { padding: 1rem 1.5rem; background-color: #f8f9fa; border-bottom-left-radius: 0.5rem; border-bottom-right-radius: 0.5rem; } /* Form Styling */ .form-group { margin-bottom: 1.25rem; } .form-control { border-radius: 0.375rem; padding: 0.625rem 0.875rem; border-color: #e2e8f0; transition: border-color 0.2s, box-shadow 0.2s; } .form-control:focus { border-color: #4e73df; box-shadow: 0 0 0 0.2rem rgba(78, 115, 223, 0.15); } /* Table Enhancements */ .table { margin-bottom: 0; } .table th { font-weight: 600; color: #4a5568; border-top: none; padding: 1rem; } .table td { padding: 1rem; vertical-align: middle; } /* Badge Enhancements */ .badge { padding: 0.5em 0.75em; font-weight: 500; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.025em; } </style> {% block extra_js %} <script> $(document).ready(function() { function formatBalance(value) { if (value == null || isNaN(value)) { return ''; } // Convert the value to a number with two decimal places const formattedValue = parseFloat(value).toFixed(2); // Split the value into the integer and decimal parts const [intPart, decPart] = formattedValue.split('.'); // Format the integer part with spaces as thousand separators const intWithSpaces = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' '); // Return the formatted balance with dot as decimal separator return `${intWithSpaces}.${decPart}`; } // Set default dates const today = new Date(); const firstDay = new Date(today.getFullYear(), today.getMonth(), 1); const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0); $('#startDate').val(firstDay.toISOString().split('T')[0]); $('#endDate').val(lastDay.toISOString().split('T')[0]); // Trigger initial filter $('#startDate').trigger('change'); // ===== Bank Fee Management ===== $('#addBankFee').click(function() { $('#feeDate').val(new Date().toISOString().split('T')[0]); $('#bankFeeModal').modal('show'); }); // Initialize presentation autocomplete $("#relatedPresentation").autocomplete({ minLength: 2, source: function(request, response) { $.ajax({ url: '{% url "presentation-autocomplete" %}', dataType: 'json', data: { term: request.term }, success: function(data) { response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); } }); }, select: function(event, ui) { $(this).val(ui.item.label); $(this).data('selected-id', ui.item.value); return false; } }); // ===== VAT Calculations ===== function calculateAmounts() { const rawAmount = parseFloat($('#rawAmount').val()) || 0; const vatRate = parseFloat($('#vatRate').val()) || 0; const vatIncluded = $('#vatIncluded').prop('checked'); let vatAmount = 0; let totalAmount = 0; if (vatRate === 0) { totalAmount = rawAmount; } else if (vatIncluded) { const vatMultiplier = (vatRate / 100) + 1; const rawAmountCalculated = rawAmount / vatMultiplier; vatAmount = rawAmount - rawAmountCalculated; totalAmount = rawAmount; $('#rawAmount').val(rawAmountCalculated.toFixed(2)); } else { vatAmount = rawAmount * (vatRate / 100); totalAmount = rawAmount + vatAmount; } $('#vatAmount').val(vatAmount.toFixed(2)); $('#totalAmount').val(totalAmount.toFixed(2)); } $('#rawAmount, #vatRate').on('input change', calculateAmounts); $('#vatIncluded').on('change', calculateAmounts); $(document).on('click', '.toggle-details', function(e) { e.preventDefault(); e.stopPropagation(); const $row = $(this).closest('tr'); const $icon = $(this).find('i'); const recordId = $row.data('record-id'); const recordType = $row.data('type'); // Create a unique identifier for unpaid entries const detailsSelector = recordType.includes('REVERSAL') ? `[data-record-id="${recordId}-reversal"]` : `[data-record-id="${recordId}"]`; const $detailsRow = $(`.details-row${detailsSelector}`); console.log('Toggle details:', { recordId, recordType, detailsSelector, detailsRowFound: $detailsRow.length }); // Toggle details with animation if ($detailsRow.hasClass('d-none')) { $detailsRow.removeClass('d-none'); $icon.removeClass('fa-chevron-down').addClass('fa-chevron-up'); } else { $detailsRow.addClass('d-none'); $icon.removeClass('fa-chevron-up').addClass('fa-chevron-down'); } }); // ===== Fee Row Collapsing ===== $(document).on('click', '.fee-row', function(e) { // Don't trigger if clicking button if ($(e.target).closest('.btn-group').length || $(e.target).is('input')) { return; } const feeId = $(this).data('fee-id'); const detailsRow = $(`.fee-details-row[data-fee-id="${feeId}"]`); const icon = $(this).find('.toggle-fee-details i'); detailsRow.toggleClass('d-none'); icon.toggleClass('fa-chevron-down fa-chevron-up'); }); // ===== Bank Fee Creation ===== $('#saveBankFee').click(async function() { if (!$('#bankFeeForm')[0].checkValidity()) { $('#bankFeeForm')[0].reportValidity(); return; } const data = { bank_account: '{{ bank_account.id }}', fee_type: $('#feeType').val(), date: $('#feeDate').val(), related_presentation: $('#relatedPresentation').data('selected-id'), raw_amount: $('#rawAmount').val(), vat_rate: $('#vatRate').val(), vat_included: $('#vatIncluded').prop('checked'), vat_amount: $('#vatAmount').val(), total_amount: $('#totalAmount').val() }; try { const response = await fetch('{% url "create-bank-fee" %}', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const result = await response.json(); if (response.ok) { $('#bankFeeModal').modal('hide'); showToast('Bank fee recorded successfully', 'success'); location.reload(); } else { showToast(result.message || 'Failed to record bank fee', 'error'); } } catch (error) { console.error('Fee creation error:', error); showToast('Failed to record bank fee', 'error'); } }); // ===== Date Range Filtering ===== $('#startDate, #endDate').on('change', function() { const startDate = $('#startDate').val(); const endDate = $('#endDate').val(); // Don't filter if one date is set and the other isn't if ((startDate && !endDate) || (!startDate && endDate)) { return; } // Don't filter if end date is before start date if (startDate && endDate && startDate > endDate) { showToast('Start date must be before end date', 'error'); return; } console.log('Applying filters:', { startDate, endDate }); // Show loading state $('#statementTableBody').html('<tr><td colspan="9" class="text-center"><div class="spinner-border text-primary" role="status"></div></td></tr>'); $.ajax({ url: window.location.pathname, method: 'GET', data: startDate || endDate ? { start_date: startDate, end_date: endDate } : {}, success: function(response) { if (response && response.html) { $('#statementTableBody').html(response.html); } if (response && response.totals) { // Update summary cards using format_balance filter $('#total-debit').text(formatBalance(response.totals.debit)); $('#total-credit').text(formatBalance(response.totals.credit)); const balance = response.totals.balance; const balanceElement = $('#final-balance'); balanceElement.text(formatBalance(Math.abs(balance))); balanceElement .removeClass('text-success text-danger') .addClass(parseFloat(balance) >= 0 ? 'text-success' : 'text-danger'); } }, error: function(xhr, status, error) { console.error('Filter error details:', { status: xhr.status, statusText: xhr.statusText, responseText: xhr.responseText, error: error }); let message = 'Failed to filter statement'; try { const response = JSON.parse(xhr.responseText); message = response.error || message; } catch(e) { console.error('Error parsing response:', e); } showToast(message, 'error'); } }); }); // Remove the form submit handler since we're using change events $('#statementFilterForm').on('submit', function(e) { e.preventDefault(); }); // ===== Transfer Management ===== let selectedRecords = new Map(); $('.record-checkbox').change(function() { const $checkbox = $(this); const recordData = { source_type: $checkbox.data('source-type'), source_id: $checkbox.data('source-id'), amount: $checkbox.data('amount'), date: $checkbox.data('date'), label: $checkbox.data('label'), reference: $checkbox.data('reference') }; if (this.checked) { selectedRecords.set(recordData.source_id, recordData); } else { selectedRecords.delete(recordData.source_id); } updateSelectionUI(); }); $('#selectAll').change(function() { $('.record-checkbox:not(:disabled)').prop('checked', this.checked).trigger('change'); }); function updateSelectionUI() { const totalAmount = Array.from(selectedRecords.values()) .reduce((sum, record) => sum + parseFloat(record.amount), 0); $('#transferBtn').prop('disabled', selectedRecords.size === 0); $('#selectedTotal').text(totalAmount.toFixed(2)); const $list = $('#selectedRecordsList'); $list.empty(); selectedRecords.forEach(record => { $list.append(` <div class="list-group-item d-flex justify-content-between align-items-center"> <div> <div class="font-weight-bold">${record.label}</div> <small class="text-muted"> ${record.date} | Ref: ${record.reference} </small> </div> <span class="text-success">${parseFloat(record.amount).toFixed(2)} MAD</span> </div> `); }); } $('#transferBtn').click(function() { $('#transferDate').val(new Date().toISOString().split('T')[0]); $('#transferModal').modal('show'); }); $('#saveTransfer').click(async function() { if (!$('#transferForm')[0].checkValidity()) { $('#transferForm')[0].reportValidity(); return; } const data = { from_bank: '{{ bank_account.id }}', to_bank: $('#toBankAccount').val(), date: $('#transferDate').val(), label: $('#transferLabel').val(), records: Array.from(selectedRecords.values()) }; try { const response = await fetch('{% url "create-transfer" %}', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const result = await response.json(); if (response.ok) { $('#transferModal').modal('hide'); showToast('Transfer created successfully', 'success'); location.reload(); } else { showToast(result.message || 'Failed to create transfer', 'error'); } } catch (error) { console.error('Transfer creation error:', error); showToast('Failed to create transfer', 'error'); } }); // Reset modals on hide $('#bankFeeModal').on('hidden.bs.modal', function() { $('#bankFeeForm')[0].reset(); $('#relatedPresentation').val('').data('selected-id', ''); $('#vatAmount').prop('readonly', true); $('#vatIncluded').prop('disabled', false); $('.is-invalid').removeClass('is-invalid'); }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); }); // ===== Global Functions ===== function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } function deleteBankFee(feeId) { if (!confirm('Are you sure you want to delete this bank fee?')) { return; } fetch(`/testapp/bank-accounts/fees/${feeId}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }) .then(response => response.json()) .then(result => { if (result.status === 'success') { showToast('Bank fee deleted successfully', 'success'); location.reload(); } else { throw new Error(result.message || 'Failed to delete bank fee'); } }) .catch(error => { console.error('Fee deletion error:', error); showToast(error.message || 'Failed to delete bank fee', 'error'); }); } function deleteTransfer(transferId) { if (!confirm('Are you sure you want to delete this transfer? This will make the transferred records available for transfer again.')) { return; } fetch(`/testapp/bank-accounts/transfers/${transferId}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }) .then(response => response.json()) .then(result => { if (result.status === 'success') { showToast('Transfer deleted successfully', 'success'); location.reload(); } else { throw new Error(result.message || 'Failed to delete transfer'); } }) .catch(error => { console.error('Transfer deletion error:', error); showToast(error.message || 'Failed to delete transfer', 'error'); }); } </script> {% endblock %}
```

# templates/bank/other_operations.html

```html
{% extends 'base.html' %} {% load accounting_filters %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ bank_account.bank }} - {{ bank_account.account_number }} Other Operations</h2> <div class="d-flex gap-2"> <!-- Filter Form --> <form class="form-inline" id="otherOpsFilterForm"> <div class="input-group"> <input type="date" class="form-control" name="start_date" id="startDate"> <input type="date" class="form-control" name="end_date" id="endDate"> <button type="submit" class="btn btn-primary">Apply</button> </div> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-6"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Debit (From On-Hold)</h5> <p class="card-text text-danger h4">{{ total_debit|format_balance }}</p> </div> </div> </div> <div class="col-md-6"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Credit (To Entity)</h5> <p class="card-text text-success h4">{{ total_credit|format_balance }}</p> </div> </div> </div> </div> <!-- Other Operations Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Label</th> <th>Description</th> <th class="text-right">Debit (From 5000)</th> <th class="text-right">Credit (To Entity)</th> <th>Reference</th> <th>Actions</th> </tr> </thead> <tbody id="otherOpsTableBody"> {% include 'bank/partials/other_operations_table.html' %} </tbody> </table> </div> </div> <script> $(document).ready(function() { $('#otherOpsFilterForm').on('submit', function(e) { e.preventDefault(); const startDate = this.querySelector('[name="start_date"]').value; const endDate = this.querySelector('[name="end_date"]').value; if (!validateDateRange(startDate, endDate)) { showToast('Start date must be before or equal to end date', 'error'); return; } $.get(window.location.pathname, $(this).serialize()) .done(function(response) { $('#otherOpsTableBody').html(response.html); }) .fail(function(xhr) { showToast('Error loading other operations data', 'error'); }); }); // Helper functions (same as above) function validateDateRange(startDate, endDate) { if (!startDate || !endDate) return true; return new Date(startDate) <= new Date(endDate); } function showToast(message, type = 'error') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } }); // View functions (same as above) function viewReceipt(type, id) { $.get(`/testapp/receipts/details/${type}/${id}/`) .done(function(response) { $('#receiptDetailModal .modal-content').html(response.html); $('#receiptDetailModal').modal('show'); }) .fail(function(xhr) { showToast('Error loading receipt details', 'error'); }); } function viewPresentation(id) { $.get(`/testapp/presentations/${id}/`) .done(function(response) { $('#presentationDetailModal .modal-content').html(response); $('#presentationDetailModal').modal('show'); }) .fail(function(xhr) { showToast('Error loading presentation details', 'error'); }); } </script> {% endblock %}
```

# templates/bank/partials/accounting_table.html

```html
{% load accounting_filters %} {% for entry in entries %} <tr class="{% if entry.entry_type == 'credit' %}table-light{% endif %}"> <td>{{ entry.date|date:"Y-m-d" }}</td> <td>{{ entry.label }}</td> <td class="text-right text-danger"> {% if entry.debit %}{{ entry.debit|format_balance }}{% endif %} </td> <td class="text-right text-success"> {% if entry.credit %}{{ entry.credit|format_balance }}{% endif %} </td> <td>{{ entry.account_code }}</td> <td>{{ entry.reference }}</td> <td>{{ entry.journal_code }}</td> <td> {% if entry.source_type == 'presentation_receipt' %} <button class="btn btn-sm btn-info" onclick="viewPresentation('{{ entry.source_id }}')"> <i class="fas fa-eye"></i> </button> {% else %} <button class="btn btn-sm btn-info" onclick="viewReceipt('{{ entry.source_type }}', '{{ entry.source_id }}')"> <i class="fas fa-eye"></i> </button> {% endif %} </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No entries found for this period</td> </tr> {% endfor %}
```

# templates/bank/partials/accounts_table.html

```html
{% load accounting_filters %} {% for account in accounts %} <tr> <td> <div class="d-flex align-items-center"> <span class="bank-logo {{ account.bank|lower }}"></span> <span class="ml-2">{{ account.get_bank_display }}</span> </div> </td> <td>{{ account.account_number }}</td> <td>{{ account.journal_number }}</td> <td>{{ account.city }}</td> <td> <span class="badge {% if account.account_type == 'national' %}badge-primary{% else %}badge-info{% endif %}"> {{ account.get_account_type_display }} </span> </td> <td> <span class="badge {% if account.is_active %}badge-success{% else %}badge-danger{% endif %}"> {{ account.is_active|yesno:"Active,Inactive" }} </span> </td> <td>{{ account.created_at|date:"d/m/Y" }}</td> <td> {% if account.is_active %} <button class="btn btn-sm btn-danger deactivate-account" data-account-id="{{ account.id }}" {% if account.has_active_checkers %}disabled{% endif %} title="{% if account.has_active_checkers %}Cannot deactivate: Has active checkers{% endif %}"> <i class="fas fa-times"></i> </button> {% endif %} </td> </tr> {% endfor %}
```

# templates/bank/partials/other_operations_table.html

```html
{% load accounting_filters %} {% for entry in entries %} {% if entry.entry_type == 'debit' %} {# Show only debit entries to avoid duplicates #} <tr> <td>{{ entry.date|date:"Y-m-d" }}</td> <td>{{ entry.label }}</td> <td> {% if "Payment" in entry.label %} <span class="badge badge-success">Paid</span> {% else %} <span class="badge badge-danger">Unpaid</span> {% endif %} </td> <td class="text-right text-danger"> {{ entry.debit|format_balance }} </td> <td class="text-right text-success"> {{ entry.credit|format_balance }} </td> <td>{{ entry.reference }}</td> <td> {% if entry.source_type == 'presentation_receipt' %} <button class="btn btn-sm btn-info" onclick="viewPresentation('{{ entry.source_id }}')"> <i class="fas fa-eye"></i> </button> {% else %} <button class="btn btn-sm btn-info" onclick="viewReceipt('{{ entry.source_type }}', '{{ entry.source_id }}')"> <i class="fas fa-eye"></i> </button> {% endif %} </td> </tr> {% endif %} {% empty %} <tr> <td colspan="7" class="text-center">No entries found for this period</td> </tr> {% endfor %}
```

# templates/bank/partials/statement_table.html

```html
{% load accounting_filters %} {% for entry in entries %} <tr class="record-row" data-record-id="{{ entry.display_id|default:entry.source_id }}" data-type="{{ entry.type|lower }}"> <td> {% if entry.can_transfer %} <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input record-checkbox" id="record{{ entry.source_id }}" data-amount="{{ entry.credit }}" data-source-type="{{ entry.source_type }}" data-source-id="{{ entry.source_id }}" data-date="{{ entry.date|date:'Y-m-d' }}" data-label="{{ entry.label }}" data-reference="{{ entry.reference }}"> <label class="custom-control-label" for="record{{ entry.source_id }}"></label> </div> {% endif %} {% if entry.is_transferred %} <span class="badge badge-info" title="Transferred"> <i class="fas fa-exchange-alt"></i> </span> {% endif %} </td> <td>{{ entry.date|date:"Y-m-d" }}</td> <td> {{ entry.label }} </td> <td> <span class="badge badge-{{ entry.type|lower }}"> {{ entry.type }} </span> </td> <td class="text-right text-danger"> {% if entry.debit %}{{ entry.debit|format_balance }}{% endif %} </td> <td class="text-right text-success"> {% if entry.credit %}{{ entry.credit|format_balance }}{% endif %} </td> <td>{{ entry.reference }}</td> <td class="text-right {% if entry.balance > 0 %}text-success{% else %}text-danger{% endif %}"> {{ entry.balance|format_balance }} </td> <td> <!-- Add a toggle button to show the details --> <button class="btn btn-sm btn-link toggle-details"> <i class="fas fa-chevron-down"></i> </button> <!-- Add your existing action buttons if needed --> {% if entry.can_delete %} {% if entry.type == 'BANK_FEE' %} <button class="btn btn-sm btn-danger" onclick="deleteBankFee('{{ entry.source_id }}')"> <i class="fas fa-trash"></i> </button> {% else %} <button class="btn btn-sm btn-danger" onclick="deleteTransfer('{{ entry.source_id }}')"> <i class="fas fa-trash"></i> </button> {% endif %} {% endif %} </td> </tr> <!-- The details row: hidden by default --> <tr class="details-row d-none" data-record-id="{{ entry.display_id|default:entry.source_id }}"> <td colspan="9"> <div class="card"> <div class="card-body"> {% if entry.type == 'BANK_FEE' %} <!-- Bank fee details --> <div class="row"> <div class="col-md-3"> <strong>Fee Type:</strong><br> {{ entry.details.fee_type }} </div> <div class="col-md-3"> <strong>Raw Amount:</strong><br> {{ entry.details.raw_amount|format_balance }} </div> <div class="col-md-3"> <strong>VAT Rate:</strong><br> {{ entry.details.vat_rate }}% </div> <div class="col-md-3"> <strong>VAT Included:</strong><br> {{ entry.details.vat_included|yesno:"Yes,No" }} </div> </div> <div class="row mt-3"> <div class="col-md-4"> <strong>VAT Amount:</strong><br> {{ entry.details.vat_amount|format_balance }} </div> <div class="col-md-4"> <strong>Total Amount:</strong><br> {{ entry.details.total_amount|format_balance }} </div> <div class="col-md-4"> <strong>Related Presentation:</strong><br> {{ entry.details.related_presentation|default:"None" }} </div> </div> {% elif entry.type == 'CASH' %} <div class="row"> <div class="col-md-3"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-3"> <strong>Client:</strong><br> {{ entry.client_name }} </div> <div class="col-md-3"> <strong>Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-3"> <strong>Operation Date:</strong><br> {{ entry.operation_date|date:"Y-m-d" }} </div> </div> {% elif entry.type == 'TRANSFER' %} <div class="row"> <div class="col-md-4"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-4"> <strong>Transfer Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-4"> <strong>Transfer Date:</strong><br> {{ entry.transfer_date|date:"Y-m-d" }} </div> </div> {% elif 'REVERSAL' in entry.type %} <div class="row"> <div class="col-md-3"> <strong>Original Discount:</strong><br> {{ entry.discount_reference }} </div> <div class="col-md-3"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-3"> <strong>Due Date:</strong><br> {{ entry.due_date|date:"Y-m-d" }} </div> <div class="col-md-3"> <strong>Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-3"> <strong>Status:</strong><br> <span class="badge badge-{{ entry.status|lower }}"> {{ entry.status }} </span> </div> </div> {% elif 'CHECK' in entry.type or 'LCN' in entry.type %} <div class="row"> <div class="col-md-3"> <strong>Entity:</strong><br> {{ entry.entity_name }} </div> <div class="col-md-3"> <strong>Due Date:</strong><br> {{ entry.due_date|date:"Y-m-d" }} </div> <div class="col-md-3"> <strong>Reference:</strong><br> {{ entry.reference }} </div> <div class="col-md-3"> <strong>Status:</strong><br> <span class="badge badge-{{ entry.status|lower }}"> {{ entry.status }} </span> </div> </div> {% endif %} </div> </div> </td> </tr> {% empty %} <tr> <td colspan="9" class="text-center">No entries found</td> </tr> {% endfor %}
```

# templates/base.html

```html
<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>{% block title %}BSK Management{% endblock %}</title> <!-- CSS --> <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet"> <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet"> <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet"> <link href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css" rel="stylesheet"> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"> <!-- Custom Styles --> <style> :root { --primary-color: #2563eb; --sidebar-width: 250px; --topbar-height: 60px; --transition-speed: 0.3s; } body { min-height: 100vh; background-color: #f8fafc; padding-top: var(--topbar-height) } /* Sidebar Styling */ #sidebar { width: var(--sidebar-width); height: 100vh; position: fixed; left: 0; top: 0; background: #1e293b; transition: transform var(--transition-speed); z-index: 1000; } #sidebar.collapsed { transform: translateX(-100%); } #sidebar .nav-link { color: #e2e8f0; padding: 0.8rem 1rem; transition: all var(--transition-speed); } #sidebar .nav-link:hover { background: rgba(255, 255, 255, 0.1); transform: translateX(5px); } #sidebar .nav-link.active { background: var(--primary-color); color: white; } /* Dropdown menu styling */ .nav-dropdown { background: rgba(255, 255, 255, 0.05); } .nav-dropdown .nav-link { padding-left: 2.5rem !important; font-size: 0.9rem; opacity: 0.9; } .nav-item-parent > .nav-link { display: flex; justify-content: space-between; align-items: center; } .nav-item-parent > .nav-link::after { content: '\f107'; font-family: 'Font Awesome 5 Free'; font-weight: 900; transition: transform 0.3s; } .nav-item-parent > .nav-link[aria-expanded="true"]::after { transform: rotate(180deg); } .collapse { transition: all 0.3s ease; } /* Main Content */ #main-content { margin-left: var(--sidebar-width); padding-top: var(--topbar-height); transition: margin var(--transition-speed); padding: 20px; margin-top: 0; } #main-content.expanded { margin-left: 0; } /* Topbar */ #topbar { height: var(--topbar-height); background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); position: fixed; top: 0; right: 0; left: var(--sidebar-width); z-index: 999; transition: left var(--transition-speed); } #topbar.expanded { left: 0; } /* Modal Animations */ .modal.fade .modal-dialog { transform: scale(0.8); transition: transform var(--transition-speed); } .modal.show .modal-dialog { transform: scale(1); } .modal { z-index: 1050; } /* Toast Animations */ .toast { position: fixed; top: 20px; right: 20px; z-index: 1050; animation: slideIn 0.3s ease-out; } @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } } /* Card Hover Effects */ .card { transition: transform 0.2s, box-shadow 0.2s; } .card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); } /* Button Hover Effects */ .btn { transition: all 0.2s; } .btn:hover { transform: translateY(-1px); } /* Table Row Hover */ .table-hover tbody tr { transition: background-color 0.2s; } /* Select2 Styling */ .select2-container--default .select2-selection--single { height: 38px; border: 1px solid #ced4da; border-radius: 0.375rem; } .select2-container--default .select2-selection--single .select2-selection__rendered { line-height: 38px; } /* Ensure dropdowns appear above other elements */ .dropdown-menu { z-index: 1000; } /* Keep autocomplete dropdown above other elements */ .ui-autocomplete { z-index: 2000; .timeline-item { opacity: 0; } .timeline-item.animate__animated { opacity: 1; } /* Custom animation for loading spinner */ @keyframes modalFadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } } .modal.show .modal-dialog { animation: modalFadeIn 0.3s ease-out; } /* Enhance timeline visuals */ .timeline-content:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); transform: translateY(-2px); transition: all 0.3s ease; } .timeline-marker::after { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: white; border-radius: 50%; } } </style> <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script> <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script> </head> <body> <!-- Sidebar --> <nav id="sidebar"> <div class="d-flex flex-column h-100"> <div class="p-3 text-center"> <h5 class="text-white mb-0">BSK Management</h5> </div> <ul class="nav flex-column mt-2"> <li class="nav-item"> <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" href="{% url 'home' %}"> <i class="fas fa-home me-2"></i> Dashboard </a> </li> <!-- Business Operations Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'business' in request.path %}active{% endif %}" data-toggle="collapse" href="#businessSubmenu" role="button" aria-expanded="false" aria-controls="businessSubmenu"> <span><i class="fas fa-briefcase me-2"></i> Business Operations</span> </a> <div class="collapse nav-dropdown" id="businessSubmenu"> <a class="nav-link {% if 'supplier' in request.path %}active{% endif %}" href="{% url 'supplier-list' %}"> <i class="fas fa-truck me-2"></i> Suppliers </a> <a class="nav-link {% if 'product' in request.path %}active{% endif %}" href="{% url 'product-list' %}"> <i class="fas fa-box-open me-2"></i> Products </a> <a class="nav-link {% if 'invoice' in request.path %}active{% endif %}" href="{% url 'invoice-list' %}"> <i class="fas fa-file-invoice-dollar me-2"></i> Invoices </a> </div> </li> <!-- Clients Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'client' in request.path %}active{% endif %}" data-toggle="collapse" href="#clientSubmenu" role="button" aria-expanded="false" aria-controls="clientSubmenu"> <span><i class="fas fa-users me-2"></i> Clients</span> </a> <div class="collapse nav-dropdown" id="clientSubmenu"> <a class="nav-link {% if 'receipt' in request.path %}active{% endif %}" href="{% url 'receipt-list' %}"> <i class="fas fa-receipt me-2"></i> Receipts </a> <a class="nav-link {% if 'client_management' in request.path %}active{% endif %}" href="{% url 'client_management' %}"> <i class="fas fa-address-card me-2"></i> Clients </a> <a class="nav-link {% if 'sale-list' in request.path %}active{% endif %}" href="{% url 'sale-list' %}"> <i class="fas fa-shopping-cart me-2"></i> Sales </a> <a class="nav-link {% if 'presentation' in request.path %}active{% endif %}" href="{% url 'presentation-list' %}"> <i class="fas fa-file-powerpoint me-2"></i> Presentations </a> </div> </li> <!-- Financial Management Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'financial' in request.path %}active{% endif %}" data-toggle="collapse" href="#financialSubmenu" role="button" aria-expanded="false" aria-controls="financialSubmenu"> <span><i class="fas fa-money-bill-wave me-2"></i> Financial Management</span> </a> <div class="collapse nav-dropdown" id="financialSubmenu"> <a class="nav-link {% if 'bank-account' in request.path %}active{% endif %}" href="{% url 'bank-account-list' %}"> <i class="fas fa-university me-2"></i> Bank Accounts </a> <a class="nav-link {% if 'checks' in request.path %}active{% endif %}" href="{% url 'check-list' %}"> <i class="fas fa-money-check me-2"></i> Checks </a> <a class="nav-link {% if 'checkers' in request.path %}active{% endif %}" href="{% url 'checker-list' %}"> <i class="fas fa-user-shield me-2"></i> Checkers </a> </div> </li> <!-- Bottom Section --> <div class="mt-auto p-3"> <div class="dropdown"> <button class="btn btn-dark dropdown-toggle w-100" type="button" data-bs-toggle="dropdown"> <i class="fas fa-user-circle me-2"></i> {{ request.user.username }} </button> <ul class="dropdown-menu dropdown-menu-dark w-100"> <li> <a class="dropdown-item" href="{% url 'profile' %}"> <i class="fas fa-id-card me-2"></i> Profile </a> </li> <li><hr class="dropdown-divider"></li> <li> <a class="dropdown-item text-danger" href="{% url 'logout' %}"> <i class="fas fa-sign-out-alt me-2"></i> Logout </a> </li> </ul> </div> </div> </div> </nav> <!-- Topbar --> <nav id="topbar" class="px-4 d-flex align-items-center"> <button id="sidebar-toggle" class="btn btn-link"> <i class="fas fa-bars"></i> </button> <div class="ms-auto d-flex align-items-center"> <div class="dropdown"> <button class="btn btn-link dropdown-toggle" type="button" data-bs-toggle="dropdown"> <i class="fas fa-bell"></i> <span class="badge bg-danger">3</span> </button> <ul class="dropdown-menu dropdown-menu-end"> <li><h6 class="dropdown-header">Notifications</h6></li> <li><a class="dropdown-item" href="#">New invoice added</a></li> <li><a class="dropdown-item" href="#">Payment received</a></li> <li><a class="dropdown-item" href="#">Check due today</a></li> </ul> </div> </div> </nav> <!-- Main Content --> <main id="main-content" class="p-4"> {% block content %}{% endblock %} </main> <!-- Scripts --> <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script> <script> $(document).ready(function() { // Sidebar Toggle $('#sidebar-toggle').click(function() { $('#sidebar').toggleClass('collapsed'); $('#main-content').toggleClass('expanded'); $('#topbar').toggleClass('expanded'); }); // Initialize Select2 $('.select2').select2({ theme: 'bootstrap' }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); // Keep submenu open if a child is active if ($('#clientSubmenu .nav-link.active').length) { $('#clientSubmenu').addClass('show'); $('#clientSubmenu').prev('.nav-link').attr('aria-expanded', 'true'); } }); // Toast function function showToast(message, type = 'success') { const toast = ` <div class="toast align-items-center text-white bg-${type}" role="alert"> <div class="d-flex"> <div class="toast-body">${message}</div> <button type="button" class="close ml-2 mb-1" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> </div> `; const toastContainer = $('<div>', { class: 'position-fixed', style: 'top: 20px; right: 20px; z-index: 1060;' }).html(toast); $('body').append(toastContainer); toastContainer.find('.toast').toast({ delay: 3000 }).toast('show'); toastContainer.find('.toast').on('hidden.bs.toast', function() { toastContainer.remove(); }); } </script> {% block extra_js %}{% endblock %} </body> </html>
```

# templates/client/client_card.html

```html
{% extends 'base.html' %} {% load accounting_filters %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ client.name }} - Client Card</h2> <!-- Period Selection --> <div class="d-flex gap-2"> <form class="form-inline" method="get"> <select name="year" class="form-control mr-2"> {% for year_choice in years %} <option value="{{ year_choice }}" {% if year_choice == selected_year %}selected{% endif %}> {{ year_choice }} </option> {% endfor %} </select> <select name="month" class="form-control mr-2"> {% for month_num, month_name in months %} <option value="{{ month_num }}" {% if month_num == selected_month %}selected{% endif %}> {{ month_name }} </option> {% endfor %} </select> <button type="submit" class="btn btn-primary">Apply</button> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <!-- Previous Balance --> <div class="col-md-3"> <div class="card"> <div class="card-body"> <h5 class="card-title">Previous Balance</h5> <p class="card-text {% if previous_balance > 0 %}text-danger{% else %}text-success{% endif %} h4"> {{ previous_balance|format_balance }} </p> </div> </div> </div> <!-- Period Movements --> <div class="col-md-6"> <div class="card"> <div class="card-body"> <h5 class="card-title">Period Movements</h5> <div class="row"> <div class="col-6"> <small class="text-muted">Debit</small> <p class="text-danger h4">{{ period_debit|format_balance }}</p> </div> <div class="col-6"> <small class="text-muted">Credit</small> <p class="text-success h4">{{ period_credit|format_balance }}</p> </div> </div> </div> </div> </div> <!-- Final Balance --> <div class="col-md-3"> <div class="card"> <div class="card-body"> <h5 class="card-title">Final Balance</h5> <p class="card-text {% if final_balance > 0 %}text-danger{% else %}text-success{% endif %} h4"> {{ final_balance|format_balance }} </p> </div> </div> </div> </div> <!-- Transactions Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Description</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th class="text-right">Balance</th> </tr> </thead> <tbody> {% for t in transactions %} <tr {% if t.type == 'BALANCE' %}class="table-info"{% endif %}> <td>{{ t.date|date:"Y-m-d" }}</td> <td>{{ t.description }}</td> <td class="text-right text-danger"> {% if t.debit %}{{ t.debit|format_balance }}{% endif %} </td> <td class="text-right text-success"> {% if t.credit %}{{ t.credit|format_balance }}{% endif %} </td> <td class="text-right {% if t.balance > 0 %}text-danger{% else %}text-success{% endif %}"> {{ t.balance|format_balance }} </td> </tr> {% empty %} <tr> <td colspan="5" class="text-center">No transactions found for this period</td> </tr> {% endfor %} </tbody> </table> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Auto-submit form when selection changes $('select[name="year"], select[name="month"]').change(function() { $(this).closest('form').submit(); }); }); </script> {% endblock %}
```

# templates/client/client_management.html

```html
{% extends 'base.html' %} {% load static %} {% block extra_css %} <link rel="stylesheet" href="{% static 'css/client.css' %}"> {% endblock %} {% block content %} <div class="container-fluid px-4"> <div class="row mt-4"> <div class="col"> <!-- Tabs Navigation --> <ul class="nav nav-tabs nav-fill border-0" id="clientTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active custom-tab" id="clients-tab" data-toggle="tab" href="#clients" role="tab"> <i class="fas fa-users me-2"></i> Clients </a> </li> <li class="nav-item"> <a class="nav-link custom-tab" id="entities-tab" data-toggle="tab" href="#entities" role="tab"> <i class="fas fa-building me-2"></i> Entities </a> </li> </ul> <!-- Tabs Content --> <div class="tab-content mt-4" id="clientTabsContent"> <!-- Clients Tab --> <div class="tab-pane fade show active" id="clients" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-users text-primary me-2"></i> Clients Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#clientModal"> <i class="fas fa-plus-circle me-2"></i> Add New Client </button> </div> <!-- Clients Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="clientsTable"> <thead class="bg-light"> <tr> <th>Client Code</th> <th>Name</th> <th>Created At</th> <th>Actions</th> </tr> </thead> <tbody id="clientsTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> <!-- Entities Tab --> <div class="tab-pane fade" id="entities" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-building text-primary me-2"></i> Entities Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#entityModal"> <i class="fas fa-plus-circle me-2"></i> Add New Entity </button> </div> <!-- Entities Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="entitiesTable"> <thead class="bg-light"> <tr> <th>Name</th> <th>ICE Code</th> <th>Accounting Code</th> <th>City</th> <th>Phone</th> <th>Actions</th> </tr> </thead> <tbody id="entitiesTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> </div> </div> </div> </div> {% include 'client/components/client_modal.html' %} {% include 'client/components/entity_modal.html' %} <script> console.log('Initializing client management module...'); // Validation configurations const ValidationConfig = { clientCode: { minLength: 5, maxLength: 10, pattern: /^\d+$/, messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 10 digits' } }, iceCode: { length: 15, pattern: /^\d+$/, inputPattern: /[0-9]/, // Add this - for single digit validation messages: { pattern: 'Only digits are allowed', length: 'Must be exactly 15 digits' } }, accountingCode: { minLength: 5, maxLength: 7, pattern: /^\d+$/, // Just check for digits initially messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 7 digits' } }, name: { pattern: /^[a-zA-Z\s]+$/, messages: { pattern: 'Only letters and spaces allowed' } } }; class FormValidator { constructor(formId, config) { this.form = document.getElementById(formId); this.config = config; console.log(`Initializing validator for form: ${formId}`); this.setupValidation(); } setupValidation() { const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { console.log(`Setting up validation for: ${input.id}`); this.setupInputValidation(input); }); } setupInputValidation(input) { const validationType = input.dataset.validate; const rules = this.config[validationType]; // Real-time validation input.addEventListener('input', (e) => { console.log(`Input event on ${input.id}`); this.validateInput(input, rules); }); // Blur validation input.addEventListener('blur', (e) => { console.log(`Blur event on ${input.id}`); this.validateInput(input, rules, true); }); // Prevent invalid characters input.addEventListener('keypress', (e) => { if (rules.pattern && !String.fromCharCode(e.charCode).match(rules.pattern)) { e.preventDefault(); } }); // Prevent invalid characters and enforce length input.addEventListener('keypress', (e) => { // Check max length for ICE code if (validationType === 'iceCode' && input.value.length >= 15) { e.preventDefault(); return; } // Special handling for first character of accounting code if (validationType === 'accountingCode') { if (input.value.length === 0 && e.key !== '3') { e.preventDefault(); return; } if (input.value.length >= 7) { e.preventDefault(); return; } } // Use inputPattern for digit validation if (!e.key.match(rules.inputPattern)) { e.preventDefault(); } }); } validateInput(input, rules, isBlur = false) { const value = input.value.trim(); let isValid = true; let message = ''; // Add validating class during check input.classList.add('is-validating'); // Required field validation if (input.required && !value) { isValid = false; message = 'This field is required'; this.updateValidationUI(input, false, message); return false; } // Special validation for accounting code if (input.dataset.validate === 'accountingCode') { if (!value.startsWith('3')) { isValid = false; message = 'Must start with 3'; } } // Uniqueness check for client_code and accounting_code on blur if (isBlur && (input.id === 'clientCode' || input.id === 'accountingCode' || input.id === 'iceCode')) { fetch(`/testapp/api/validate/${input.id}/${value}/`) .then(response => response.json()) .then(data => { if (!data.available) { isValid = false; message = `This ${input.id.replace('Code', ' code')} already exists`; this.updateValidationUI(input, false, message, true); } }) .catch(error => { console.error(`Error checking ${input.id} uniqueness:`, error); }); } // Pattern validation if (rules.pattern && !value.match(rules.pattern)) { isValid = false; message = rules.messages.pattern; } // Length validation if (rules.length && value.length !== rules.length) { isValid = false; message = rules.messages.length; } if (rules.minLength && value.length < rules.minLength) { isValid = false; message = rules.messages.minLength; } if (rules.maxLength && value.length > rules.maxLength) { isValid = false; message = rules.messages.maxLength; } // Update UI with validation result setTimeout(() => { input.classList.remove('is-validating'); this.updateValidationUI(input, isValid, message, isBlur); this.checkFormValidity(); }, 300); return isValid; } checkFormValidity() { let isValid = true; const formId = this.formId; const form = document.querySelector(`#${formId}:not(.d-none), #${formId}:not(.hide)`); if (!form) { console.debug(`Form ${formId} not found or not visible`); return true; } const inputs = form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { // Check for empty required fields if (input.required && !input.value.trim()) { isValid = false; return; } // Check for validation state if (input.classList.contains('is-invalid') || (input.required && !input.classList.contains('is-valid'))) { isValid = false; return; } }); // Update save button state const saveButton = form.querySelector('button[type="submit"]'); if (saveButton) { saveButton.disabled = !isValid; console.debug(`Form ${formId} validity: ${isValid}`); } return isValid; } updateValidationUI(input, isValid, message, isBlur) { const feedback = input.nextElementSibling; if (isValid) { input.classList.remove('is-invalid'); input.classList.add('is-valid'); if (feedback && feedback.classList.contains('invalid-feedback')) { feedback.classList.remove('show'); } } else if (isBlur || input.value.length > 0) { input.classList.remove('is-valid'); input.classList.add('is-invalid'); if (feedback) { feedback.textContent = message; feedback.classList.add('show'); } } } validateForm() { let isValid = true; const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { const validationType = input.dataset.validate; const rules = this.config[validationType]; if (!this.validateInput(input, rules, true)) { isValid = false; } }); return isValid; } } // Client Management class class ClientManagement { constructor() { console.log('Initializing ClientManagement'); this.initializeValidators(); this.bindEvents(); this.loadClients(); this.loadEntities(); } initializeValidators() { this.clientValidator = new FormValidator('clientForm', ValidationConfig); this.entityValidator = new FormValidator('entityForm', ValidationConfig); } // Event Binding bindEvents() { $('#saveClientBtn').on('click', () => this.saveClient()); $('#saveEntityBtn').on('click', () => this.saveEntity()); // Reset forms on modal close $('#clientModal').on('hidden.bs.modal', () => this.resetForm('clientForm')); $('#entityModal').on('hidden.bs.modal', () => this.resetForm('entityForm')); // Tab change handlers $('#clientTabs a[data-toggle="tab"]').on('shown.bs.tab', (e) => { if (e.target.id === 'clients-tab') { this.loadClients(); } else { this.loadEntities(); } }); } // Client Operations async loadClients() { console.log('Loading clients...'); try { const response = await fetch('/testapp/api/clients/'); const data = await response.json(); const tbody = $('#clientsTableBody'); tbody.empty(); data.clients.forEach(client => { const formattedDate = this.formatDate(client.created_at); tbody.append(` <tr class="fade-in"> <td>${client.client_code}</td> <td>${client.name}</td> <td>${formattedDate}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editClient('${client.id}', '${client.name}', '${client.client_code}')"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger me-2" onclick="window.clientManagement.deleteClient('${client.id}')"> <i class="fas fa-trash"></i> </button> <a href="/testapp/clients/${client.id}/card/" class="btn btn-sm btn-outline-info"> <i class="fas fa-chart-line me-1"></i> Sales Card </a> </td> </tr> `); console.log('Client loaded:', client, formattedDate); }); } catch (error) { console.error('Error loading clients:', error); this.showToast('Error', 'Failed to load clients'); } } async saveClient() { console.log('Saving client...'); if (!this.clientValidator.validateForm()) { console.log('Client form validation failed'); return; } const formData = { name: $('#clientName').val().trim(), client_code: $('#clientCode').val().trim() }; const id = $('#clientId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/clients/${id}/update/` : '/testapp/api/clients/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Client saved successfully:', result); $('#clientModal').modal('hide'); await this.loadClients(); this.showToast('Success', 'Client saved successfully'); } } catch (error) { console.error('Error saving client:', error); this.showToast('Error', error.message); } } editClient(id, name, client_code) { console.log('Editing client:', id); $('#clientId').val(id); $('#clientName').val(name); $('#clientCode').val(client_code); $('#clientModalTitle .title-text').text('Edit Client'); $('#clientModal').modal('show'); } async deleteClient(id) { if (!confirm('Are you sure you want to delete this client?')) { return; } try { const response = await this.sendRequest( `/testapp/api/clients/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadClients(); this.showToast('Success', 'Client deleted successfully'); } } catch (error) { console.error('Error deleting client:', error); this.showToast('Error', error.message); } } // Entity Operations async loadEntities() { console.log('Loading entities...'); try { const response = await fetch('/testapp/api/entities/'); const data = await response.json(); const tbody = $('#entitiesTableBody'); tbody.empty(); data.entities.forEach(entity => { tbody.append(` <tr class="fade-in"> <td>${entity.name}</td> <td>${entity.ice_code}</td> <td>${entity.accounting_code}</td> <td>${entity.city || '-'}</td> <td>${entity.phone_number || '-'}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editEntity('${entity.id}', ${JSON.stringify(entity)})"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger" onclick="window.clientManagement.deleteEntity('${entity.id}')"> <i class="fas fa-trash"></i> </button> </td> </tr> `); }); } catch (error) { console.error('Error loading entities:', error); this.showToast('Error', 'Failed to load entities'); } } async saveEntity() { console.log('Saving entity...'); if (!this.entityValidator.validateForm()) { console.log('Entity form validation failed'); return; } const formData = { name: $('#entityName').val().trim(), ice_code: $('#iceCode').val().trim(), accounting_code: $('#accountingCode').val().trim(), city: $('#city').val().trim(), phone_number: $('#phoneNumber').val().trim() }; const id = $('#entityId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/entities/${id}/update/` : '/testapp/api/entities/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Entity saved successfully:', result); $('#entityModal').modal('hide'); await this.loadEntities(); this.showToast('Success', 'Entity saved successfully'); } } catch (error) { console.error('Error saving entity:', error); this.showToast('Error', error.message); } } editEntity(id, entityData) { console.log('Editing entity:', id); $('#entityId').val(id); $('#entityName').val(entityData.name); $('#iceCode').val(entityData.ice_code); $('#accountingCode').val(entityData.accounting_code); $('#city').val(entityData.city || ''); $('#phoneNumber').val(entityData.phone_number || ''); $('#entityModalTitle .title-text').text('Edit Entity'); $('#entityModal').modal('show'); } async deleteEntity(id) { if (!confirm('Are you sure you want to delete this entity?')) { return; } try { const response = await this.sendRequest( `/testapp/api/entities/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadEntities(); this.showToast('Success', 'Entity deleted successfully'); } } catch (error) { console.error('Error deleting entity:', error); this.showToast('Error', error.message); } } // Utility Methods formatDate(dateString) { if (!dateString) return '-'; try { const date = new Date(dateString); return date.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); } catch (e) { console.error('Error formatting date:', e); return dateString; } } async sendRequest(url, method, data = null) { const options = { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }; if (data && method !== 'GET') { options.body = JSON.stringify(data); } const response = await fetch(url, options); if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'Request failed'); } return response; } resetForm(formId) { console.log(`Resetting form: ${formId}`); const form = document.getElementById(formId); form.reset(); const inputs = form.querySelectorAll('.form-control'); inputs.forEach(input => { input.classList.remove('is-valid', 'is-invalid', 'is-validating'); const feedback = input.nextElementSibling; if (feedback) { feedback.classList.remove('show'); } }); // Reset titles if (formId === 'clientForm') { $('#clientModalTitle .title-text').text('Add New Client'); $('#clientId').val(''); } else { $('#entityModalTitle .title-text').text('Add New Entity'); $('#entityId').val(''); } } showToast(title, message) { // You can replace this with your preferred notification library alert(`${title}: ${message}`); } } // Initialize when document is ready document.addEventListener('DOMContentLoaded', () => { console.log('Initializing client management module'); window.clientManagement = new ClientManagement(); }); </script> {% endblock %}
```

# templates/client/components/client_modal.html

```html
<!-- Client Modal --> <div class="modal fade" id="clientModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="clientModalTitle"> <i class="fas fa-user-plus me-2"></i> <span class="title-text"> Add New Client</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="clientForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="clientId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="clientName" class="form-label"> <i class="fas fa-signature me-2"></i> Client Name </label> <input type="text" class="form-control" id="clientName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- Client Code Field --> <div class="form-group mb-4"> <label for="clientCode" class="form-label"> <i class="fas fa-hashtag me-2"></i> Client Code </label> <input type="text" class="form-control" id="clientCode" data-validate="clientCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Enter a unique code (5-10 digits) </small> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i> Cancel </button> <button type="button" class="btn btn-primary" id="saveClientBtn"> <i class="fas fa-save me-2"></i> Save Client </button> </div> </div> </div> </div>
```

# templates/client/components/entity_modal.html

```html
<!-- Entity Modal --> <div class="modal fade" id="entityModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="entityModalTitle"> <i class="fas fa-building me-2"></i> <span class="title-text"> Add New Entity</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="entityForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="entityId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="entityName" class="form-label"> <i class="fas fa-signature me-2"></i> Entity Name </label> <input type="text" class="form-control" id="entityName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- ICE Code Field --> <div class="form-group mb-4"> <label for="iceCode" class="form-label"> <i class="fas fa-fingerprint me-2"></i> ICE Code </label> <input type="text" class="form-control" id="iceCode" data-validate="iceCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must be exactly 15 digits </small> </div> <!-- Accounting Code Field --> <div class="form-group mb-4"> <label for="accountingCode" class="form-label"> <i class="fas fa-calculator me-2"></i> Accounting Code </label> <input type="text" class="form-control" id="accountingCode" data-validate="accountingCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must start with 3 and be 5-7 digits long </small> </div> <!-- Optional Fields --> <div class="row"> <div class="col-md-6"> <div class="form-group mb-4"> <label for="city" class="form-label"> <i class="fas fa-city me-2"></i> City </label> <input type="text" class="form-control" id="city"> </div> </div> <div class="col-md-6"> <div class="form-group mb-4"> <label for="phoneNumber" class="form-label"> <i class="fas fa-phone me-2"></i> Phone Number </label> <input type="tel" class="form-control" id="phoneNumber"> </div> </div> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i> Cancel </button> <button type="button" class="btn btn-primary" id="saveEntityBtn"> <i class="fas fa-save me-2"></i> Save Entity </button> </div> </div> </div> </div>
```

# templates/client/sale_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Client Sales</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#saleModal"> <i class="fas fa-plus"></i> New Sale </button> </div> <!-- Sales Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Type</th> <th>Amount</th> <th>Notes</th> </tr> </thead> <tbody> {% for sale in sales %} <tr> <td>{{ sale.date|date:"Y-m-d" }}</td> <td>{{ sale.client.name }}</td> <td>{{ sale.get_sale_type_display }}</td> <td class="text-right">{{ sale.amount|floatformat:2 }}</td> <td>{{ sale.notes }}</td> </tr> {% empty %} <tr> <td colspan="4" class="text-center">No sales recorded yet</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Sale Modal --> <div class="modal fade" id="saleModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Record New Sale</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="saleForm"> {% csrf_token %} <div class="form-group"> <label for="client">Client</label> <input type="text" class="form-control" id="client" placeholder="Search client..." required> <input type="hidden" id="client_id" name="client" required> </div> <div class="form-group"> <label for="date">Date</label> <input type="date" class="form-control" id="date" name="date" value="{% now 'Y-m-d' %}" required> </div> <div class="form-group"> <label for="sale_type">Sale Type</label> <select class="form-control" id="sale_type" name="sale_type" required> <option value="BRICKS">Bricks</option> <option value="TRANSPORT">Transport</option> </select> </div> <div class="form-group"> <label for="amount">Amount</label> <input type="number" class="form-control" id="amount" name="amount" step="0.01" min="0.01" required> </div> <div class="form-group"> <label for="notes">Notes</label> <textarea class="form-control" id="notes" name="notes" rows="2"></textarea> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveSale">Save</button> </div> </div> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 2, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Handle form submission $('#saveSale').click(function() { const form = $('#saleForm'); $.ajax({ url: "{% url 'create-sale' %}", method: 'POST', data: form.serialize(), success: function(response) { $('#saleModal').modal('hide'); showToast('Sale recorded successfully'); location.reload(); }, error: function(xhr) { showToast(xhr.responseJSON.message, 'error'); } }); }); }); </script> {% endblock %}
```


# templates/presentation/available_receipts.html

```html
{% load accounting_filters %} <div class="receipt-container"> <!-- Summary info --> <div class="alert alert-info"> <strong>Selected:</strong> <span id="selectedCount">0</span> receipts <strong class="ml-3">Total Amount:</strong> <span id="selectedAmount">0.00</span> MAD </div> <!-- Receipts table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="selectAll"> <label class="custom-control-label" for="selectAll"></label> </div> </th> <th>Reference</th> <th>Entity</th> <th>Issue Date</th> <th>Due Date</th> <th>Amount</th> <th>Days to Due</th> <th>Status</th> </tr> </thead> <tbody> {% for receipt in receipts %} <!-- In available_receipts.html --> <tr> <td> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input receipt-checkbox" id="receipt{{ receipt.id }}" value="{{ receipt.id }}" data-amount="{{ receipt.amount }}"> <label class="custom-control-label" for="receipt{{ receipt.id }}"></label> </div> </td> <td>{{ receipt.get_receipt_number }}</td> <td>{{ receipt.entity.name }}</td> <td>{{ receipt.operation_date|date:"Y-m-d" }}</td> <td>{{ receipt.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ receipt.amount|format_balance }}</td> <td> {% with days_to_due=receipt.due_date|timeuntil %} {{ days_to_due }} {% endwith %} </td> <td> <span class="badge badge-{{ receipt.status|lower }}"> {{ receipt.get_status_display }} </span> {% if receipt.status == 'UNPAID' and receipt.last_presentation_date %} <br> <small class="text-muted"> Previously presented on {{ receipt.last_presentation_date|date:"Y-m-d" }} </small> {% endif %} </td> </tr> {% endfor %} </tbody> </table> </div> </div> <script> $(document).ready(function() { // Handle select all checkbox $('#selectAll').change(function() { $('.receipt-checkbox').prop('checked', $(this).prop('checked')); updateSelection(); }); // Handle individual checkboxes $('.receipt-checkbox').change(function() { updateSelection(); // Update select all checkbox state $('#selectAll').prop('checked', $('.receipt-checkbox').length === $('.receipt-checkbox:checked').length); }); function updateSelection() { const selected = $('.receipt-checkbox:checked'); $('#selectedCount').text(selected.length); const totalAmount = selected.toArray() .reduce((sum, checkbox) => sum + parseFloat($(checkbox).data('amount')), 0); $('#selectedAmount').text(totalAmount.toFixed(2)); // Enable/disable save button based on selection $('#savePresentation').prop('disabled', selected.length === 0); } }); </script>
```

# templates/presentation/partials/presentations_table.html

```html
<!-- templates/presentation/partials/presentations_table.html --> {% load accounting_filters %} {% load presentation_filters %} {% for presentation in presentations %} <tr> <td>{{ presentation.date|date:"Y-m-d" }}</td> <td>{{ presentation.get_presentation_type_display }}</td> <td>{{ presentation.bank_account.bank }} - {{ presentation.bank_account.account_number }}</td> <td>{{ presentation.bank_reference|default:"-" }}</td> <td class="text-right">{{ presentation.total_amount|format_balance }}</td> <td>{{ presentation.receipt_count }}</td> <td> <span class="badge badge-{{ presentation.status|status_badge }}"> {{ presentation.get_status_display }} </span> </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewPresentation('{{ presentation.id }}')"> <i class="fas fa-eye"></i> </button> <button class="btn btn-sm btn-primary" onclick="editPresentation('{{ presentation.id }}')" {% if presentation.status == 'paid' %}disabled{% endif %}> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger" onclick="deletePresentation('{{ presentation.id }}')" {% if presentation.status != 'pending' %}disabled{% endif %}> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No presentations found</td> </tr> {% endfor %}
```

# templates/presentation/presentation_detail_modal.html

```html
{% load presentation_filters %} {% load accounting_filters %} <!-- Debug info --> {% comment %} Available filters: {{ presentation_filters }} {% endcomment %} <!-- Test filter directly --> {% with test_status='pending' %} Raw status: {{ test_status }} Filtered status: {{ test_status|status_badge }} {% endwith %} <div id="presentation-container" data-presentation-id="{{ presentation.id }}"> <div class="modal-header"> <h5 class="modal-title"> {{ presentation.get_presentation_type_display }} Presentation Details </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Presentation Info --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <p><strong>Date:</strong> {{ presentation.date|date:"Y-m-d" }}</p> <p><strong>Bank Account:</strong> {{ presentation.bank_account }}</p> <p><strong>Total Amount:</strong> {{ presentation.total_amount|format_balance }}</p> </div> <div class="col-md-6 d-flex flex-column"> {% if presentation.status == 'pending' %} <div class="form-group"> <label>Bank Reference</label> <input type="text" class="form-control" id="bankReference" value="{{ presentation.bank_reference }}" required> </div> <div class="form-group"> <label>Status</label> <select class="form-control" id="presentationStatus"> <option value="presented">Presented</option> <option value="discounted">Discounted</option> <option value="rejected">Rejected</option> </select> </div> {% else %} <p><strong>Bank Reference:</strong> {{ presentation.bank_reference }}</p> <p><strong>Status:</strong> <span class="badge badge-{{ presentation.status|status_badge }}"> {{ presentation.get_status_display }} </span> </p> {% endif %} <p><strong>Notes:</strong> {{ presentation.notes|default:"No notes" }}</p> </div> </div> </div> </div> <!-- Receipts Table --> <h6>Presented Receipts</h6> <div class="table-responsive"> <table class="table table-sm"> <thead> <tr> <th>Type</th> <th>Reference</th> <th>Entity</th> <th>Client</th> <th>Due Date</th> <th class="text-right">Amount</th> <th>Status</th> {% if presentation.status == 'presented' %} <th>New Status</th> {% endif %} </tr> </thead> <tbody> {% for receipt in presentation.presentation_receipts.all %} <tr> <td> {% if receipt.checkreceipt %} <i class="fas fa-money-check"></i> Check {% else %} <i class="fas fa-file-invoice-dollar"></i> LCN {% endif %} </td> <td> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.check_number }} <br><small class="text-muted">{{ receipt.checkreceipt.get_issuing_bank_display }}</small> {% else %} {{ receipt.lcn.lcn_number }} <br><small class="text-muted">{{ receipt.lcn.get_issuing_bank_display }}</small> {% endif %} </td> <td> <strong> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.entity.name }} {% else %} {{ receipt.lcn.entity.name }} {% endif %} </strong> <br> <small class="text-muted"> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.entity.ice_code }} {% else %} {{ receipt.lcn.entity.ice_code }} {% endif %} </small> </td> <td> <small> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.client.name }} {% else %} {{ receipt.lcn.client.name }} {% endif %} </small> </td> <td> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.due_date|date:"Y-m-d" }} {% else %} {{ receipt.lcn.due_date|date:"Y-m-d" }} {% endif %} </td> <td class="text-right">{{ receipt.amount|format_balance }}</td> <td> {% if receipt.checkreceipt %} <span class="badge badge-{{ receipt.checkreceipt.status|status_badge }}"> {{ receipt.checkreceipt.get_status_display }} </span> {% if receipt.checkreceipt.status == 'UNPAID' and receipt.checkreceipt.rejection_cause %} <br><small class="text-danger">{{ receipt.checkreceipt.get_rejection_cause_display}}</small> {% endif %} {% if receipt.checkreceipt.compensation_info %} <br><small class="text-muted">{{ receipt.checkreceipt.compensation_info }}</small> {% endif %} {% else %} <span class="badge badge-{{ receipt.lcn.status|status_badge }}"> {{ receipt.lcn.get_status_display }} </span> {% if receipt.lcn.status == 'UNPAID' and receipt.lcn.rejection_cause %} <br><small class="text-danger">{{ receipt.lcn.get_rejection_cause_display }}</small> {% endif %} {% if receipt.lcn.compensation_info %} <br><small class="text-muted">{{ receipt.lcn.compensation_info }}</small> {% endif %} {% endif %} </td> {% if presentation.status == 'presented' or presentation.status == 'discounted' %} <td> <select class="form-control form-control-sm receipt-status" data-receipt-id="{{ receipt.id }}" {% if receipt.recorded_status %}disabled{% endif %}> <option value="">Pending</option> <option value="paid" {% if receipt.recorded_status == 'PAID' or receipt.checkreceipt.status == 'PAID' or receipt.lcn.status == 'PAID' %}selected{% endif %}>Paid</option> <option value="unpaid" {% if receipt.recorded_status == 'UNPAID' or receipt.checkreceipt.status == 'UNPAID' or receipt.lcn.status == 'UNPAID' %}selected{% endif %}>Unpaid</option> </select> </td> {% endif %} </tr> {% endfor %} </tbody> <tfoot> <tr class="font-weight-bold"> <td colspan="5" class="text-right">Total:</td> <td class="text-right">{{ presentation.total_amount|format_balance }}</td> <td colspan="2"></td> </tr> </tfoot> </table> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> {% if presentation.status == 'pending' %} <button type="button" class="btn btn-primary" onclick="updatePresentation('{{ presentation.id }}')"> Update Status </button> {% endif %} {% if presentation.status == 'presented' or presentation.status == 'discounted' %} <button type="button" class="btn btn-primary" onclick="updateReceiptStatuses('{{ presentation.id }}')"> Update Statuses </button> {% endif %} </div> <!-- Unpaid Cause Modal --> <div class="modal fade" id="unpaidCauseModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Rejection Cause</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="form-group mb-3"> <label for="rejectionCause">Select Cause</label> <select class="form-control" id="rejectionCause" required> <option value="">Select a cause...</option> {% for cause, label in rejection_causes %} <option value="{{ cause }}">{{ label }}</option> {% endfor %} </select> </div> <div class="form-group"> <label for="unpaidDate">Unpaid Date</label> <input type="date" class="form-control" id="unpaidDate" required> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="confirmCause">Confirm</button> </div> </div> </div> </div> </div> <script> const presentationId = '{{ presentation.id }}'; console.log("Presentation ID:", presentationId); function updatePresentation(id) { const bankRef = $('#bankReference').val(); if (!bankRef) { showError('Bank reference is required'); return; } const data = { bank_reference: bankRef, status: $('#presentationStatus').val() }; $.ajax({ url: `/testapp/presentations/${id}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, contentType: 'application/json', data: JSON.stringify(data), success: function(response) { location.reload(); }, error: function(xhr) { showError(xhr.responseJSON?.message || 'Update failed'); } }); } // Handle receipt status changes // Handle receipt status updates function updateReceiptStatuses(presentationId) { console.log('Updating receipt statuses for presentation:', presentationId); const receiptStatuses = {}; let hasChanges = false; let pendingUnpaidStatus = null; // Debug info for all receipt status selects $('.receipt-status').each(function() { const $select = $(this); console.log('Found receipt status select:', { receiptId: $select.data('receipt-id'), currentValue: $select.val(), disabled: $select.prop('disabled'), options: Array.from($select.find('option')).map(opt => ({ value: opt.value, text: opt.text, selected: opt.selected })) }); }); $('.receipt-status').each(function() { const $select = $(this); const receiptId = $select.data('receipt-id'); const status = $select.val(); console.log('Processing receipt:', { receiptId: receiptId, newStatus: status, previousStatus: $select.data('previous-status') }); if (status === 'unpaid') { pendingUnpaidStatus = { receiptId: receiptId, $select: $select }; console.log('Found pending unpaid status:', pendingUnpaidStatus); return false; // Break the loop } if (status) { receiptStatuses[receiptId] = status; hasChanges = true; console.log(`Adding status update for receipt ${receiptId}:`, status); } }); if (pendingUnpaidStatus) { console.log('Showing unpaid cause modal for:', pendingUnpaidStatus); $('#unpaidCauseModal').modal('show').data('pendingStatus', pendingUnpaidStatus); return; } if (!hasChanges) { console.log('No status changes detected'); showToast('No status changes to update', 'info'); return; } console.log('Submitting status updates:', receiptStatuses); submitStatusUpdates(presentationId, receiptStatuses); } function submitStatusUpdates(presentationId, receiptStatuses) { console.log('Submitting status updates:', { presentationId: presentationId, statuses: receiptStatuses, url: `/testapp/presentations/${presentationId}/edit/` }); $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value, 'Content-Type': 'application/json' }, data: JSON.stringify({ receipt_statuses: receiptStatuses }), success: function(response) { console.log('Status update response:', response); // Update UI to reflect changes Object.entries(receiptStatuses).forEach(([receiptId, status]) => { const $select = $(`.receipt-status[data-receipt-id="${receiptId}"]`); console.log(`Updating UI for receipt ${receiptId}:`, { status: status, select: $select.length ? 'found' : 'not found' }); if ($select.length) { $select.prop('disabled', true) .val(status); // Update the badge in the status column const $statusCell = $select.closest('tr').find('td:nth-last-child(2)'); const statusClass = status === 'paid' ? 'badge-success' : 'badge-danger'; $statusCell.html(`<span class="badge ${statusClass}">${status.toUpperCase()}</span>`); } }); showToast('Receipt statuses updated successfully', 'success'); // Reload after a short delay to ensure UI is updated setTimeout(() => { location.reload(); }, 1000); }, error: function(xhr) { console.error('Status update failed:', { status: xhr.status, response: xhr.responseText }); try { const error = JSON.parse(xhr.responseText); showToast(error.message || 'Failed to update statuses', 'error'); } catch (e) { showToast('Failed to update statuses', 'error'); } } }); } // Handle unpaid cause confirmation $('#confirmCause').click(function() { console.log('Confirm cause button clicked'); const cause = $('#rejectionCause').val(); const unpaidDate = $('#unpaidDate').val(); console.log('Selected cause:', cause); console.log('Selected date:', unpaidDate); if (!cause) { console.log('Error: No cause selected'); showError('Please select a rejection cause'); return; } if (!unpaidDate) { console.log('Error: No date selected'); showError('Please select an unpaid date'); return; } const pendingStatus = $('#unpaidCauseModal').data('pendingStatus'); console.log('Retrieved pending status:', pendingStatus); if (!pendingStatus || !pendingStatus.receiptId) { console.log('Error: Missing pending status data', { pendingStatus }); showError('Missing receipt information'); return; } const receiptStatuses = { [pendingStatus.receiptId]: { status: 'unpaid', cause: cause, unpaid_date: unpaidDate } }; console.log('Submitting status update:', receiptStatuses); submitStatusUpdates(presentationId, receiptStatuses); $('#unpaidCauseModal').modal('hide'); }); function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } function showError(message) { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-danger text-white"> <strong class="mr-auto">Error</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .html(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', function() { container.remove(); }); } </script>
```

# templates/presentation/presentation_list.html

```html
{% extends 'base.html' %} {% load presentation_filters %} {% load accounting_filters %} {% block content %} {% csrf_token %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Presentations</h2> <div class="btn-group"> <button class="btn btn-primary dropdown-toggle" data-toggle="dropdown"> <i class="fas fa-plus"></i> New Presentation </button> <div class="dropdown-menu dropdown-menu-right"> <a class="dropdown-item" href="#" onclick="startPresentation('check')"> <i class="fas fa-money-check"></i> Present Checks </a> <a class="dropdown-item" href="#" onclick="startPresentation('lcn')"> <i class="fas fa-file-invoice-dollar"></i> Present LCNs </a> </div> </div> </div> <!-- Presentations Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Type</th> <th>Bank Account</th> <th>Bank Reference</th> <th class="text-right" style="min-width: 120px;">Total Amount</th> <th>Receipt Count</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for presentation in presentations %} <tr> <td>{{ presentation.date|date:"Y-m-d" }}</td> <td>{{ presentation.get_presentation_type_display }}</td> <td>{{ presentation.bank_account.bank }} - {{ presentation.bank_account.account_number }}</td> <td>{{ presentation.bank_reference|default:"-" }}</td> <td class="text-right" style="min-width: 120px;">{{ presentation.total_amount|format_balance }}</td> <td class="text-center">{{ presentation.receipt_count }}</td> <td> <span class="badge badge-{{ presentation.status|status_badge }}"> {{ presentation.get_status_display }} </span> </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewPresentation('{{ presentation.id }}')"> <i class="fas fa-eye"></i> </button> <button class="btn btn-sm btn-primary" onclick="editPresentation('{{ presentation.id }}')" {% if presentation.status == 'paid' %}disabled{% endif %}> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger" onclick="deletePresentation('{{ presentation.id }}')" {% if presentation.status != 'pending' %}disabled{% endif %}> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No presentations found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Create/Edit Presentation Modal --> <div class="modal fade" id="presentationModal" tabindex="-1"> <div class="modal-dialog modal-xl"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <span id="modalTitleText">Create Presentation</span> </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="presentationForm"> <!-- Step indicator --> <div class="mb-4"> <div class="progress"> <div class="progress-bar" role="progressbar" style="width: 0%"></div> </div> <div class="d-flex justify-content-between mt-2"> <span class="step-indicator active">1. Basic Info</span> <span class="step-indicator">2. Select Receipts</span> <span class="step-indicator">3. Review</span> </div> </div> <!-- Step 1: Basic Info --> <div id="step1" class="step-content"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Presentation Type</label> <select class="form-control" id="presentationType" required> <option value="COLLECTION">Collection</option> <option value="DISCOUNT">Discount</option> </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Bank Account</label> <select class="form-control" id="bankAccount" required> {% for account in bank_accounts %} <option value="{{ account.id }}"> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Date</label> <input type="date" class="form-control" id="presentationDate" value="{% now 'Y-m-d' %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Notes</label> <textarea class="form-control" id="presentationNotes" rows="1"></textarea> </div> </div> </div> </div> <!-- Discount Line Information (Only shown if type is DISCOUNT) --> <div class="discount-info d-none mb-3"> <h6 class="card-subtitle mb-3">Discount Line Information</h6> <div class="row"> <div class="col-md-3"> <div class="card text-white bg-info mb-3"> <div class="card-body"> <h5 class="card-title">Total Discount Line</h5> <p class="card-text"> <span id="totalDiscountLine">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-success mb-3"> <div class="card-body"> <h5 class="card-title">Used Amount</h5> <p class="card-text"> <span id="usedDiscountAmount">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-warning mb-3"> <div class="card-body"> <h5 class="card-title">Available Amount</h5> <p class="card-text"> <span id="availableDiscountAmount">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-primary mb-3"> <div class="card-body"> <h5 class="card-title">Selected Amount</h5> <p class="card-text"> <span id="selectedDiscountAmount">0.00</span> MAD </p> </div> </div> </div> </div> <div class="alert alert-danger d-none" id="discountLineExceededAlert"> The selected amount exceeds the available discount line. </div> </div> <!-- Step 2: Receipt Selection --> <div id="step2" class="step-content d-none"> <div class="receipt-selection-container"> <!-- Receipts will be loaded here --> </div> </div> <!-- Step 3: Review --> <div id="step3" class="step-content d-none"> <div class="review-summary"> <!-- Summary will be populated dynamically --> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-info" id="prevStep" style="display: none"> <i class="fas fa-arrow-left"></i> Previous </button> <button type="button" class="btn btn-primary" id="nextStep"> Next <i class="fas fa-arrow-right"></i> </button> <button type="button" class="btn btn-success" id="savePresentation" style="display: none"> <i class="fas fa-save"></i> Create Presentation </button> </div> </div> </div> </div> <!-- View Presentation Modal --> <div class="modal fade" id="viewPresentationModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Content will be loaded dynamically --> </div> </div> </div> {% endblock %} {% block extra_js %} <script> var bankAccountsList = [ {value: '', label: 'Select Bank Account'}, {% for account in bank_accounts %} { value: "{{ account.id }}", label: "{{ account.get_bank_display }} - {{ account.account_number }}" }{% if not forloop.last %},{% endif %} {% endfor %} ]; function showError(error) { console.error(error); alert('An error occurred: ' + error); } function showSuccess(message) { console.log(message); alert('Succes!: ' + message); } const PresentationManager = { currentStep: 1, totalSteps: 3, receiptType: null, selectedReceipts: [], init() { this.bindEvents(); this.setupValidation(); }, discountInfo: { available: 0, total: 0, used: 0, selected: 0 }, async loadDiscountInfo(bankAccountId) { if (!bankAccountId) return; try { const response = await fetch(`/testapp/presentations/discount-info/${bankAccountId}/?type=${this.receiptType}`); const data = await response.json(); this.discountInfo = { available: parseFloat(data.available_amount), total: parseFloat(data.total_amount), used: parseFloat(data.used_amount), selected: 0 }; this.updateDiscountDisplay(); NumberFormatter.updateDiscountDisplay(); } catch (error) { console.error('Failed to load discount information:', error); } }, updateDiscountDisplay() { const discountCard = $('.discount-info'); const presentationType = $('#presentationType').val(); if (presentationType === 'DISCOUNT') { discountCard.removeClass('d-none'); $('#totalDiscountLine').text(this.discountInfo.total.toFixed(2)); $('#usedDiscountAmount').text(this.discountInfo.used.toFixed(2)); $('#availableDiscountAmount').text(this.discountInfo.available.toFixed(2)); $('#selectedDiscountAmount').text(this.discountInfo.selected.toFixed(2)); const exceededAlert = $('#discountLineExceededAlert'); if (this.discountInfo.selected > this.discountInfo.available) { exceededAlert.removeClass('d-none'); $('#nextStep, #savePresentation').prop('disabled', true); } else { exceededAlert.addClass('d-none'); this.validateCurrentStep(); } } else { discountCard.addClass('d-none'); } }, bindEvents() { $('#nextStep').on('click', () => this.nextStep()); $('#prevStep').on('click', () => this.previousStep()); $('#savePresentation').on('click', () => this.savePresentation()); }, setupValidation() { $('#presentationForm input[required], #presentationForm select[required]') .on('input change', () => this.validateCurrentStep()); $('#presentationType, #bankAccount').on('change', () => { if ($('#presentationType').val() === 'DISCOUNT') { this.loadDiscountInfo($('#bankAccount').val()); } else { $('.discount-info').addClass('d-none'); } }); }, startPresentation(type) { this.receiptType = type; this.currentStep = 1; this.selectedReceipts = []; // Update modal title $('#modalTitleText').text(`Create ${type.toUpperCase()} Presentation`); // Reset form $('#presentationForm')[0].reset(); // Show first step this.showStep(1); // Show modal $('#presentationModal').modal('show'); }, async loadAvailableReceipts() { try { const response = await $.get('/testapp/presentations/available-receipts/', { type: this.receiptType, presentation_type: $('#presentationType').val() }); $('.receipt-selection-container').html(response.html); this.initializeReceiptSelection(); } catch (error) { showError('Failed to load available receipts'); } }, initializeReceiptSelection() { $('.receipt-checkbox').on('change', () => { this.updateSelectionSummary(); if ($('#presentationType').val() === 'DISCOUNT') { this.discountInfo.selected = Array.from($('.receipt-checkbox:checked')) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); this.updateDiscountDisplay(); NumberFormatter.updateDiscountDisplay(); } }); $('#selectAll').on('change', (e) => { $('.receipt-checkbox').prop('checked', e.target.checked); this.updateSelectionSummary(); if ($('#presentationType').val() === 'DISCOUNT') { this.discountInfo.selected = e.target.checked ? Array.from($('.receipt-checkbox')) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0) : 0; this.updateDiscountDisplay(); NumberFormatter.updateDiscountDisplay(); } }); }, updateSelectionSummary() { const selected = $('.receipt-checkbox:checked'); const count = selected.length; const total = Array.from(selected) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); $('#selectedCount').text(count); $('#selectedAmount').text(total.toFixed(2)); // Enable/disable next button based on selection $('#nextStep').prop('disabled', count === 0); }, validateCurrentStep() { let isValid = true; if (this.currentStep === 1) { // Check required fields in step 1 $('#step1 [required]').each(function() { if (!$(this).val()) { isValid = false; return false; // break } }); } else if (this.currentStep === 2) { // Check if at least one receipt is selected isValid = $('.receipt-checkbox:checked').length > 0; } $('#nextStep').prop('disabled', !isValid); return isValid; }, updateProgressBar() { const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100; $('.progress-bar').css('width', `${progress}%`); // Update step indicators $('.step-indicator').removeClass('active'); $(`.step-indicator:nth-child(${this.currentStep})`).addClass('active'); }, showStep(step) { $('.step-content').addClass('d-none'); $(`#step${step}`).removeClass('d-none'); // Update buttons $('#prevStep').toggle(step > 1); $('#nextStep').toggle(step < this.totalSteps); $('#savePresentation').toggle(step === this.totalSteps); // Load receipts if moving to step 2 if (step === 2) { this.loadAvailableReceipts(); } else if (step === 3) { this.showReviewStep(); } this.currentStep = step; this.updateProgressBar(); this.validateCurrentStep(); }, showReviewStep() { const selected = $('.receipt-checkbox:checked'); const count = selected.length; const total = Array.from(selected) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); const summary = ` <div class="card"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Presentation Summary</h6> <dl class="row mb-0"> <dt class="col-sm-4">Type</dt> <dd class="col-sm-8">${$('#presentationType option:selected').text()}</dd> <dt class="col-sm-4">Bank Account</dt> <dd class="col-sm-8">${$('#bankAccount option:selected').text()}</dd> <dt class="col-sm-4">Date</dt> <dd class="col-sm-8">${$('#presentationDate').val()}</dd> <dt class="col-sm-4">Receipts</dt> <dd class="col-sm-8">${count} ${this.receiptType}(s)</dd> <dt class="col-sm-4">Total Amount</dt> <dd class="col-sm-8">${total.toFixed(2)} MAD</dd> </dl> </div> </div> `; $('.review-summary').html(summary); }, nextStep() { if (this.validateCurrentStep()) { this.showStep(this.currentStep + 1); } }, previousStep() { if (this.currentStep > 1) { this.showStep(this.currentStep - 1); } }, async savePresentation() { try { const data = { presentation_type: $('#presentationType').val(), date: $('#presentationDate').val(), bank_account: $('#bankAccount').val(), notes: $('#presentationNotes').val(), receipt_type: this.receiptType, receipt_ids: $('.receipt-checkbox:checked').map(function() { return $(this).val(); }).get() }; console.log('Sending data:', data); const response = await $.ajax({ url: '/testapp/presentations/create/', method: 'POST', contentType: 'application/json', data: JSON.stringify(data) }); if (response.status === 'success') { $('#presentationModal').modal('hide'); showSuccess('Presentation created successfully'); location.reload(); } else { showError(response.message); } } catch (error) { console.error('Creation error:', error); const errorMessage = error.responseJSON?.message || 'Failed to create presentation'; showError(errorMessage); } }, }; class PresentationFilters { constructor() { console.log('PresentationFilters', 'Initializing filters'); this.currentFilters = {}; this.createFilterUI(); this.initializeFilters(); } getFilterConfig() { return [ { type: 'presentation_type', icon: 'tag', label: 'Type', col: 3, isSelect: true, options: [ {value: '', label: 'All Types'}, {value: 'COLLECTION', label: 'Collection'}, {value: 'DISCOUNT', label: 'Discount'} ] }, { type: 'bank_account', icon: 'university', label: 'Bank Account', col: 3, isSelect: true, options: [ {value: '', label: 'All Banks'}, ...bankAccountsList ] }, { type: 'bank_reference', icon: 'hashtag', label: 'Bank Reference', col: 3 }, { type: 'date_from', icon: 'calendar', label: 'Date From', col: 3, isDate: true }, { type: 'date_to', icon: 'calendar', label: 'Date To', col: 3, isDate: true }, { type: 'receipt_number', icon: 'receipt', label: 'Receipt Number', col: 3 } ]; } createFilterUI() { console.log('PresentationFilters', 'Creating filter UI'); const filters = this.getFilterConfig(); let filterElements = []; filters.forEach(filter => { filterElements.push(this.createFilterElement(filter)); }); const filterHtml = ` <div class="card mb-4" id="presentation-filters"> <div class="card-header d-flex justify-content-between align-items-center bg-light"> <h6 class="mb-0">Filters</h6> <div class="btn-group"> <button type="button" class="btn btn-outline-secondary btn-sm" id="presentation-reset-filters"> <i class="fas fa-undo me-1"></i>Reset </button> <button type="button" class="btn btn-outline-primary btn-sm toggle-filters"> <i class="fas fa-filter me-1"></i>Show Filters </button> </div> </div> <div class="card-body filter-content" style="display: none;"> <div class="row g-3"> ${filterElements.join('')} </div> </div> </div>`; // Insert before the table-responsive div instead of using tab $('.table-responsive').before(filterHtml); // Set up toggle button $('#presentation-filters .toggle-filters').click(() => { const $content = $('#presentation-filters .filter-content'); const $button = $('#presentation-filters .toggle-filters'); $content.slideToggle(300, () => { $button.html( $content.is(':visible') ? '<i class="fas fa-filter me-1"></i>Hide Filters' : '<i class="fas fa-filter me-1"></i>Show Filters' ); }); }); // Set up reset button $('#presentation-reset-filters').click(() => { this.resetFilters(); }); } createFilterElement(filter) { console.log('Creating filter element:', filter); if (filter.isSelect) { return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <select class="form-control" id="presentation-${filter.type}-filter"> ${filter.options.map(opt => ` <option value="${opt.value}">${opt.label}</option> `).join('')} </select> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } else if (filter.isDate) { return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <input type="date" class="form-control" id="presentation-${filter.type}-filter"> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <input type="text" class="form-control" id="presentation-${filter.type}-filter"> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } initializeFilters() { console.log('PresentationFilters', 'Initializing filter handlers'); const filters = this.getFilterConfig(); filters.forEach(filter => { const elementId = `#presentation-${filter.type}-filter`; if (filter.isSelect || filter.isDate) { $(elementId).on('change', () => { const value = $(elementId).val(); console.log('Filter', `${filter.type} changed:`, value); this.updateFilter(filter.type, value); }); if (filter.isDate) { $(elementId).on('blur', () => { if (!$(elementId).val()) { console.log('Filter', `${filter.type} input emptied on blur`); this.updateFilter(filter.type, ''); } }); } } else { let timeout; $(elementId).on('input', (e) => { clearTimeout(timeout); timeout = setTimeout(() => { console.log('Filter', `${filter.type} input:`, e.target.value); this.updateFilter(filter.type, e.target.value); }, 300); }); $(elementId).on('blur', (e) => { if (!e.target.value) { console.log('Filter', `${filter.type} input emptied on blur`); this.updateFilter(filter.type, ''); } }); } }); } updateFilter(type, value) { console.log('Filter', `Updating ${type} filter with value:`, value); if (value === '' || value === null || value === undefined) { console.log('Filter', `Removing ${type} filter due to empty value`); delete this.currentFilters[type]; } else { console.log('Filter', `Setting ${type} filter to:`, value); this.currentFilters[type] = value; } console.log('Filter', 'Current filters state:', this.currentFilters); this.applyFilters(); } applyFilters() { console.log('PresentationFilters', 'Applying filters:', this.currentFilters); $.get('/testapp/presentations/filter/', this.currentFilters) .done(response => { console.log('PresentationFilters', 'Filter response received'); $('.table-responsive tbody').html(response.html); }) .fail(error => { console.error('Filter error:', error); }); } resetFilters() { console.log('PresentationFilters', 'Resetting all filters'); const filters = this.getFilterConfig(); filters.forEach(filter => { const $element = $(`#presentation-${filter.type}-filter`); if ($element.is('select')) { $element.val('').trigger('change'); } else { $element.val('').trigger('blur'); } }); this.currentFilters = {}; this.applyFilters(); } } const NumberFormatter = { formatCurrency: (amount) => { return new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount); }, updateDiscountDisplay: function() { ['totalDiscountLine', 'usedDiscountAmount', 'availableDiscountAmount', 'selectedDiscountAmount'].forEach(id => { const element = document.getElementById(id); if (element) { const value = parseFloat(element.textContent); if (!isNaN(value)) { element.textContent = this.formatCurrency(value); } } }); } } async function viewPresentation(id) { try { const response = await $.get(`/testapp/presentations/${id}/`); $('#viewPresentationModal .modal-content').html(response); $('#viewPresentationModal').modal('show'); } catch (error) { showError('Failed to load presentation details'); } } async function editPresentation(id) { try { const data = { bank_reference: $('#bankReference').val(), status: $('#presentationStatus').val(), notes: $('#presentationNotes').val() // If you have this field }; console.log('Sending edit request:', { id: id, data: data, url: `/testapp/presentations/${id}/edit/` }); const response = await fetch(`/testapp/presentations/${id}/edit/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const responseData = await response.json(); console.log('Edit response:', responseData); if (!response.ok) { throw new Error(responseData.message || 'Failed to edit presentation'); } showSuccess('Presentation updated successfully'); $('#viewPresentationModal').modal('hide'); location.reload(); } catch (error) { console.error('Edit error:', error); showError(error.message || 'Failed to edit presentation'); } } async function deletePresentation(id) { console.log('Delete initiated for presentation:', id); try { if (!confirm('Are you sure you want to delete this presentation?')) { console.log('Delete cancelled by user'); return; } const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; console.log('CSRF token obtained:', csrfToken ? 'Yes' : 'No'); const response = await fetch(`/testapp/presentations/${id}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' } }); console.log('Delete response status:', response.status); const data = await response.json(); console.log('Delete response data:', data); if (response.ok) { showSuccess('Presentation deleted successfully'); location.reload(); } else { throw new Error(data.message || 'Failed to delete presentation'); } } catch (error) { console.error('Delete error:', error); showError(error.message || 'Failed to delete presentation'); } } // Initialize on document ready $(document).ready(function() { PresentationManager.init(); window.presentationFilters = new PresentationFilters(); }); // Global function to start presentation creation function startPresentation(type) { PresentationManager.startPresentation(type); } // Handle receipt status updates $(document).on('click', '.update-receipt-status', function() { const $button = $(this); const receiptId = $button.data('receipt-id'); if (!confirm('This action cannot be undone. Continue?')) { return; } console.log('Updating receipt status:', receiptId); $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, contentType: 'application/json', data: JSON.stringify({ receipt_id: receiptId, receipt_status: 'paid' }), success: function(response) { console.log('Status updated:', response); $button.prop('disabled', true).text('Paid'); }, error: function(xhr) { console.error('Update failed:', xhr.responseText); showToast('Failed to update status', 'error'); } }); }); </script> {% endblock %}
```

# templates/receipt/partials/cash_list.html

```html
{% load status_filters %} {% load accounting_filters %} {% for cash in receipts %} <tr> <td>{{ cash.operation_date|date:"Y-m-d" }}</td> <td>{{ cash.entity.name }}</td> <td>{{ cash.client.name }}</td> <td>{{ cash.reference_number }}</td> <td>{{ cash.credited_account.bank }} - {{ cash.credited_account.account_number }}</td> <td class="text-right">{{ cash.amount|format_balance }}</td> <td> <div class="btn-group"> {% if cash.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="cash" data-action="edit" data-id="{{ cash.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if cash.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="cash" data-id="{{ cash.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </td> </tr> {% empty %} <tr> <td colspan="6" class="text-center">No cash receipts found</td> </tr> {% endfor %}
```

# templates/receipt/partials/checks_list.html

```html
{% load status_filters %} {% for check in receipts %} <tr class="status-{{ check.status|lower }}"> <td>{{ check.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ check.entity.name }}</strong><br> <small class="text-muted">{{ check.entity.ice_code }}</small> </td> <td> <small>{{ check.client.name }}</small> </td> <td>{{ check.check_number }}</td> <td>{{ check.get_issuing_bank_display }}</td> <td>{{ check.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ check.amount|floatformat:2 }}</td> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ check.status|status_badge }}"> {{ check.get_status_display }} </span> {% if check.status == 'UNPAID' and check.rejection_cause %} <br><small class="text-danger">{{ check.get_rejection_cause_display }}</small> {% with last_pres=check.check_presentations.last %} {% if last_pres %} <br><small class="text-muted">Represented on {{ last_pres.presentation.date|date:"Y-m-d" }}</small> {% endif %} {% endwith %} {% endif %} {% if check.compensation_info %} <br><small class="text-muted">{{ check.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('check', '{{ check.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=check.check_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="check" data-action="edit" data-id="{{ check.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="check" data-id="{{ check.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No checks found</td> </tr> {% endfor %}
```

# templates/receipt/partials/lcns_list.html

```html
{% load status_filters %} {% for lcn in receipts %} <tr class="status-{{ lcn.status|lower }}"> <td>{{ lcn.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ lcn.entity.name }}</strong><br> <small class="text-muted">{{ lcn.entity.ice_code }}</small> </td> <td> <small>{{ lcn.client.name }}</small> </td> <td>{{ lcn.lcn_number }}</td> <td>{{ lcn.get_issuing_bank_display }}</td> <td>{{ lcn.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ lcn.amount|floatformat:2 }}</td> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ lcn.status|status_badge }}"> {{ lcn.get_status_display }} </span> {% if lcn.status == 'UNPAID' and lcn.rejection_cause %} <br><small class="text-danger">{{ lcn.get_rejection_cause_display }}</small> {% endif %} {% if lcn.compensation_info %} <br><small class="text-muted">{{ lcn.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('lcn', '{{ lcn.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=lcn.lcn_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="lcn" data-action="edit" data-id="{{ lcn.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="lcn" data-id="{{ lcn.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No LCNs found</td> </tr> {% endfor %}
```

# templates/receipt/partials/transfers_list.html

```html
{% load status_filters %} {% for transfer in receipts %} <tr> <td>{{ transfer.operation_date|date:"Y-m-d" }}</td> <td>{{ transfer.client.name }}</td> <td>{{ transfer.transfer_reference }}</td> <td>{{ transfer.transfer_date|date:"Y-m-d" }}</td> <td>{{ transfer.credited_account.bank }} - {{ transfer.credited_account.account_number }}</td> <td class="text-right">{{ transfer.amount|floatformat:2 }}</td> <td> <div class="btn-group"> {% if transfer.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="transfer" data-action="edit" data-id="{{ transfer.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if transfer.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="transfer" data-id="{{ transfer.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </td> </tr> {% empty %} <tr> <td colspan="7" class="text-center">No transfers found</td> </tr> {% endfor %}
```

# templates/receipt/receipt_form_modal.html

```html
<!-- Debug Info --> <div style="display:none"> Receipt type from context: {{ receipt_type }} Is transfer? {% if receipt_type == 'transfer' %}Yes{% else %}No{% endif %} </div> <!-- Modal Header --> <div class="modal-header bg-gradient-primary text-white"> <h5 class="modal-title"> {% if receipt_type == 'check' %} <i class="fas fa-money-check me-2"></i> {% elif receipt_type == 'lcn' %} <i class="fas fa-file-invoice-dollar me-2"></i> {% elif receipt_type == 'cash' %} <i class="fas fa-money-bill me-2"></i> {% else %} <i class="fas fa-exchange-alt me-2"></i> {% endif %} {{ title }} </h5> <button type="button" class="btn-close btn-close-white" data-dismiss="modal"></button> </div> <div class="modal-body bg-light"> <form id="receiptForm" method="post" action="{% if receipt %}{% url 'receipt-edit' receipt_type receipt.id %}{% else %}{% url 'receipt-create' receipt_type %}{% endif %}"> {% csrf_token %} <!-- Basic Information Card --> <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-info-circle me-2"></i> Basic Information </h6> </div> <div class="card-body"> <div class="row g-3"> <div class="col-md-6"> <div class="form-floating"> <input type="text" class="form-control" id="client" name="client_display" required placeholder="Search client..." value="{% if receipt %}{{ receipt.client.name }}{% endif %}"> <label for="client"> <i class="fas fa-user text-primary me-2"></i> Client </label> <input type="hidden" id="client_id" name="client" value="{% if receipt %}{{ receipt.client.id }}{% endif %}"> </div> </div> <div class="col-md-6"> <div class="form-floating"> <input type="text" class="form-control" id="entity" name="entity_display" required placeholder="Search entity..." value="{% if receipt %}{{ receipt.entity.name }}{% endif %}"> <label for="entity"> <i class="fas fa-building text-primary me-2"></i> Entity </label> <input type="hidden" id="entity_id" name="entity" value="{% if receipt %}{{ receipt.entity.id }}{% endif %}"> </div> </div> </div> </div> </div> <!-- Transaction Details Card --> <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-file-invoice me-2"></i> Transaction Details </h6> </div> <div class="card-body"> <div class="row g-3"> <div class="col-md-4"> <div class="form-floating"> <input type="date" class="form-control" id="operation_date" name="operation_date" required value="{% if receipt %}{{ receipt.operation_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}"> <label for="operation_date"> <i class="fas fa-calendar text-primary me-2"></i> Operation Date </label> </div> </div> <div class="col-md-4"> <div class="form-floating"> <select class="form-control" id="client_year" name="client_year" required> {% for year in year_choices %} <option value="{{ year }}" {% if receipt and receipt.client_year == year or year == current_year %}selected{% endif %}> {{ year }} </option> {% endfor %} </select> <label for="client_year"> <i class="fas fa-calendar-alt text-primary me-2"></i> Year </label> </div> </div> <div class="col-md-4"> <div class="form-floating"> <select class="form-control" id="client_month" name="client_month" required> {% for month in month_choices %} <option value="{{ month.0 }}" {% if receipt and receipt.client_month == month.0 or month.0 == current_month %}selected{% endif %}> {{ month.1 }} </option> {% endfor %} </select> <label for="client_month"> <i class="fas fa-calendar-day text-primary me-2"></i> Month </label> </div> </div> <div class="col-md-6"> <div class="form-floating"> <input type="number" class="form-control" id="amount" name="amount" required step="0.01" min="0.01" value="{% if receipt %}{{ receipt.amount }}{% endif %}"> <label for="amount"> <i class="fas fa-coins text-primary me-2"></i> Amount </label> </div> </div> {% if receipt_type == 'check' or receipt_type == 'lcn' %} <div class="col-md-6"> <div class="form-floating"> <input type="text" class="form-control" id="issuingBank" name="issuing_bank_display" required placeholder="Select bank..." value="{% if receipt %}{{ receipt.get_issuing_bank_display }}{% endif %}"> <label for="issuingBank"> <i class="fas fa-university text-primary me-2"></i> Issuing Bank </label> <input type="hidden" id="issuingBankCode" name="issuing_bank" value="{% if receipt %}{{ receipt.issuing_bank }}{% endif %}"> </div> </div> {% endif %} </div> </div> </div> <!-- Receipt Specific Details Card --> {% if receipt_type == 'check' or receipt_type == 'lcn' %} <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-receipt me-2"></i> {{ receipt_type|upper }} Details </h6> </div> <div class="card-body"> <div class="row g-3"> <div class="col-md-6"> <div class="form-floating"> {% if receipt_type == 'check' %} <input type="text" class="form-control" id="check_number" name="check_number" required value="{% if receipt %}{{ receipt.check_number }}{% endif %}"> <label for="check_number"> <i class="fas fa-hashtag text-primary me-2"></i> Check Number </label> {% elif receipt_type == 'lcn' %} <input type="text" class="form-control" id="lcn_number" name="lcn_number" required value="{% if receipt %}{{ receipt.lcn_number }}{% endif %}"> <label for="lcn_number"> <i class="fas fa-hashtag text-primary me-2"></i> LCN Number </label> {% endif %} </div> </div> <div class="col-md-6"> <div class="form-floating"> <input type="date" class="form-control" id="due_date" name="due_date" required value="{% if receipt %}{{ receipt.due_date|date:'Y-m-d' }}{% endif %}"> <label for="due_date"> <i class="fas fa-clock text-primary me-2"></i> Due Date </label> </div> </div> {% if receipt_type == 'check' %} <div class="col-md-6"> <div class="form-floating"> <input type="text" class="form-control" id="branch" name="branch" value="{% if receipt %}{{ receipt.branch }}{% endif %}"> <label for="branch"> <i class="fas fa-code-branch text-primary me-2"></i> Branch </label> </div> </div> {% endif %} </div> </div> </div> {% endif %} {% if receipt_type == 'cash' or receipt_type == 'transfer' %} <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-receipt me-2"></i> {{ receipt_type|title }} Details </h6> </div> <div class="card-body"> <div class="row g-3"> <div class="col-12"> <div class="form-floating"> <select class="form-control" id="credited_account" name="credited_account" required> {% for account in bank_accounts %} <option value="{{ account.id }}" {% if receipt and receipt.credited_account.id == account.id %}selected{% endif %}> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> <label for="credited_account"> <i class="fas fa-university text-primary me-2"></i> Credited Account </label> </div> </div> {% if receipt_type == 'transfer' %} <div class="col-md-6"> <div class="form-floating"> <input type="text" class="form-control" id="transfer_reference" name="transfer_reference" required value="{% if receipt %}{{ receipt.transfer_reference }}{% endif %}"> <label for="transfer_reference"> <i class="fas fa-hashtag text-primary me-2"></i> Transfer Reference </label> </div> </div> <div class="col-md-6"> <div class="form-floating"> <input type="date" class="form-control" id="transfer_date" name="transfer_date" required value="{% if receipt %}{{ receipt.transfer_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}"> <label for="transfer_date"> <i class="fas fa-calendar-check text-primary me-2"></i> Transfer Date </label> </div> </div> {% endif %} </div> </div> </div> {% endif %} <!-- Compensation Details Card --> <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-sync me-2"></i> Compensation Details </h6> </div> <div class="card-body"> <div class="form-floating"> <input type="text" class="form-control" id="compensate-receipt-autocomplete" name="compensates" placeholder="Search for unpaid receipt..."> <label for="compensate-receipt-autocomplete"> <i class="fas fa-search text-primary me-2"></i> Compensate Unpaid Receipt </label> <input type="hidden" id="compensate-receipt-id" name="compensates"> </div> <div id="compensation-details" class="mt-2 small text-muted"></div> </div> </div> <!-- Notes Card --> <div class="card shadow-sm mb-4"> <div class="card-header bg-white"> <h6 class="mb-0 text-primary"> <i class="fas fa-sticky-note me-2"></i> Additional Notes </h6> </div> <div class="card-body"> <div class="form-floating"> <textarea class="form-control" id="notes" name="notes" rows="3" style="height: 100px">{% if receipt %}{{ receipt.notes }}{% endif %}</textarea> <label for="notes">Notes</label> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-light" data-dismiss="modal"> <i class="fas fa-times me-2"></i> Cancel </button> <button type="submit" class="btn btn-primary" form="receiptForm"> <i class="fas fa-save me-2"></i> Save Receipt </button> </div> <style> .modal-header.bg-gradient-primary { background: linear-gradient(45deg, #4e73df, #224abe); } .form-floating > label { padding-left: 1.75rem; } .form-floating > .form-control { padding-left: 2.5rem; } .form-floating > .form-control:focus { border-color: #4e73df; box-shadow: 0 0 0 0.2rem rgba(78,115,223,.25); } .card { border: none; transition: transform 0.2s ease-in-out; } .card:hover { transform: translateY(-2px); } .card-header { border-bottom: 2px solid rgba(0,0,0,.05); background-color: #fff; } .form-control { border-radius: 0.5rem; } .form-floating .invalid-feedback { margin-left: 2.5rem; } .btn-close-white { filter: brightness(0) invert(1); } .text-primary { color: #4e73df !important; } /* Autocomplete dropdown styling */ .ui-autocomplete { max-height: 200px; overflow-y: auto; z-index: 9999; border-radius: 0.5rem; border: 1px solid rgba(0,0,0,.1); box-shadow: 0 0.5rem 1rem rgba(0,0,0,.15); } .ui-autocomplete .ui-menu-item { padding: 0.5rem 1rem; border-bottom: 1px solid rgba(0,0,0,.05); } .ui-autocomplete .ui-menu-item:last-child { border-bottom: none; } .ui-autocomplete .ui-menu-item:hover { background-color: #f8f9fa; cursor: pointer; } </style> <!-- Initialize autocomplete --> <script> console.log('Form loaded for receipt type:', '{{ receipt_type }}'); $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 0, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 0, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Bank selection using jQuery UI autocomplete const banksList = [ {% for code, name in bank_choices %} { label: '{{ name }}', value: '{{ code }}' }, {% endfor %} ]; $("#issuingBank").autocomplete({ source: banksList, minLength: 0, // Show all options even without typing select: function(event, ui) { $("#issuingBank").val(ui.item.label); $("#issuingBankCode").val(ui.item.value); return false; } }).focus(function() { // Show all options when field is focused $(this).autocomplete("search", ""); }); // Add dropdown indicator and click handler $("#issuingBank").after('<span class="bank-dropdown-toggle"><i class="fas fa-chevron-down"></i></span>'); $(".bank-dropdown-toggle").click(function() { $("#issuingBank").focus(); }); $("#compensate-receipt-autocomplete").autocomplete({ source: function(request, response) { console.log('Unpaid Receipt search term:', request.term); $.ajax({ url: "{% url 'unpaid-receipt-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Unpaid Receipt data received:', data); response($.map(data.results, function(item) { return { label: item.description, value: item.description, // Display full description id: item.id }; })); }, error: function(xhr, status, error) { console.error('Unpaid Receipt autocomplete error:', error); console.log('XHR response:', xhr.responseText); } }); }, minLength: 0, select: function(event, ui) { console.log('Unpaid Receipt selected:', ui.item); $("#compensate-receipt-id").val(ui.item.id); $("#compensate-receipt-autocomplete").val(ui.item.label); $("#compensation-details").html(` Selected Receipt: ${ui.item.label} `); }, change: function(event, ui) { console.log('Unpaid Receipt change event triggered'); if (!ui.item) { $("#compensate-receipt-id").val(''); $("#compensate-receipt-autocomplete").val(''); $("#compensation-details").empty(); } } }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); // Enhanced status badges with tooltips function updateStatusBadge($element, status, details) { const badge = $('<span>') .addClass(`badge badge-${status.toLowerCase()}`) .text(status); if (details) { badge.attr('data-toggle', 'tooltip') .attr('data-html', 'true') .attr('title', details); } $element.html(badge); badge.tooltip(); } // Add bulk action support let selectedReceipts = new Set(); // Add checkboxes for bulk actions $('.receipt-table').find('tbody tr').each(function() { const $tr = $(this); const receiptId = $tr.data('receipt-id'); const $checkbox = $('<input>', { type: 'checkbox', class: 'receipt-checkbox', 'data-receipt-id': receiptId }); $tr.prepend($('<td>').append($checkbox)); }); // Bulk action handlers $('.receipt-checkbox').on('change', function() { const receiptId = $(this).data('receipt-id'); if (this.checked) { selectedReceipts.add(receiptId); } else { selectedReceipts.delete(receiptId); } updateBulkActionButtons(); }); function updateBulkActionButtons() { const hasSelected = selectedReceipts.size > 0; $('.bulk-action-btn').prop('disabled', !hasSelected); } // Add number formatting function formatCurrency(amount) { return new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(amount); } // Update all amount displays $('.amount-display').each(function() { const amount = $(this).data('amount'); $(this).text(formatCurrency(amount)); }); class ReceiptValidator { constructor(formId) { this.form = document.getElementById(formId); this.submitBtn = this.form.querySelector('button[type="submit"]'); this.fields = { client: { element: this.form.querySelector('#client'), required: true, validate: value => value.trim().length > 0 }, entity: { element: this.form.querySelector('#entity'), required: true, validate: value => value.trim().length > 0 }, amount: { element: this.form.querySelector('#amount'), required: true, validate: value => { const num = parseFloat(value); return !isNaN(num) && num > 0; } }, operation_date: { element: this.form.querySelector('#operation_date'), required: true, validate: value => value.trim().length > 0 } }; // Add type-specific validations if (this.form.querySelector('#check_number')) { this.fields.check_number = { element: this.form.querySelector('#check_number'), required: true, validate: value => value.trim().length > 0 }; this.fields.due_date = { element: this.form.querySelector('#due_date'), required: true, validate: value => { if (!value) return false; const dueDate = new Date(value); const today = new Date(); return dueDate >= today; } }; } if (this.form.querySelector('#lcn_number')) { this.fields.lcn_number = { element: this.form.querySelector('#lcn_number'), required: true, validate: value => value.trim().length > 0 }; } if (this.form.querySelector('#transfer_reference')) { this.fields.transfer_reference = { element: this.form.querySelector('#transfer_reference'), required: true, validate: value => value.trim().length > 0 }; } this.setupValidation(); } setupValidation() { Object.entries(this.fields).forEach(([name, field]) => { const element = field.element; if (!element) return; element.addEventListener('input', () => this.validateField(name)); element.addEventListener('blur', () => this.validateField(name)); }); // Validate all fields on form submit this.form.addEventListener('submit', (e) => { const isValid = this.validateAll(); if (!isValid) { e.preventDefault(); } }); } validateField(fieldName) { const field = this.fields[fieldName]; if (!field || !field.element) return true; const value = field.element.value; const isValid = field.validate(value); field.element.classList.remove('is-valid', 'is-invalid'); field.element.classList.add(isValid ? 'is-valid' : 'is-invalid'); this.updateSubmitButton(); return isValid; } validateAll() { let isValid = true; Object.keys(this.fields).forEach(fieldName => { if (!this.validateField(fieldName)) { isValid = false; } }); return isValid; } updateSubmitButton() { this.submitBtn.disabled = !this.validateAll(); } } $('#receiptModal').on('shown.bs.modal', function() { new ReceiptValidator('receiptForm'); }); }); </script> <style> .bank-dropdown-toggle { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); cursor: pointer; } .ui-autocomplete { max-height: 200px; overflow-y: auto; overflow-x: hidden; z-index: 9999; /* Scrollbar styles */ scrollbar-width: thin; scrollbar-color: #0b4d71 #f1f1f1; -webkit-overflow-scrolling: touch; -ms-overflow-style: -ms-autohiding-scrollbar; } .ui-autocomplete::-webkit-scrollbar { width: 6px; } .ui-autocomplete::-webkit-scrollbar-track { background: #f1f1f1; } .ui-autocomplete::-webkit-scrollbar-thumb { background: #888; } .ui-autocomplete::-webkit-scrollbar-thumb:hover { background: #555; } </style>
```

# templates/receipt/receipt_list.html

```html
{% extends 'base.html' %} {% load presentation_filters %} {% load accounting_filters %} <!-- Debug info --> {% comment %} Available filters: {{ presentation_filters }} {% endcomment %} {% block content %} <div class="container-fluid px-4"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-receipt text-primary me-2"></i> Receipts Management </h2> <div class="btn-group"> <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"> <i class="fas fa-plus-circle"></i> New Receipt </button> <div class="dropdown-menu"> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="check"> <i class="fas fa-money-check"></i> Check </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="lcn"> <i class="fas fa-file-invoice-dollar"></i> LCN </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="cash"> <i class="fas fa-money-bill"></i> Cash </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="transfer"> <i class="fas fa-exchange-alt"></i> Transfer </a> </div> </div> </div> <!-- Tabs Navigation --> <ul class="nav nav-tabs" id="receiptTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active" id="checks-tab" data-toggle="tab" href="#checks" role="tab"> <i class="fas fa-money-check"></i> Checks </a> </li> <li class="nav-item"> <a class="nav-link" id="lcns-tab" data-toggle="tab" href="#lcns" role="tab"> <i class="fas fa-file-invoice-dollar"></i> LCNs </a> </li> <li class="nav-item"> <a class="nav-link" id="cash-tab" data-toggle="tab" href="#cash" role="tab"> <i class="fas fa-money-bill"></i> Cash </a> </li> <li class="nav-item"> <a class="nav-link" id="transfers-tab" data-toggle="tab" href="#transfers" role="tab"> <i class="fas fa-exchange-alt"></i> Transfers </a> </li> </ul> <!-- Tab Content --> <div class="tab-content mt-4" id="receiptTabsContent"> <!-- Checks Tab Content --> <div class="tab-pane fade show active" id="checks" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>Check Number</th> <th>Issuing Bank</th> <th>Due Date</th> <th class="text-right" style="min-width: 120px;">Amount</th> <th>Bank Issued To</th> <th>Presentation</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for check in receipts.checks %} <tr class="status-{{ check.status|lower }}"> <td>{{ check.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ check.entity.name }}</strong><br> <small class="text-muted">{{ check.entity.ice_code }}</small> </td> <td> <small>{{ check.client.name }}</small> </td> <td>{{ check.check_number }}</td> <td>{{ check.get_issuing_bank_display }}</td> <td>{{ check.due_date|date:"Y-m-d" }}</td> <td class="text-right" style="min-width: 120px;">{{ check.amount|format_balance }}</td> <!-- Bank Issued To column --> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ check.status|status_badge }}"> {{ check.get_status_display }} </span> {% if check.status == 'UNPAID' and check.rejection_cause %} <br><small class="text-danger">{{ check.get_rejection_cause_display }}</small> {% with last_pres=check.check_presentations.last %} {% if last_pres %} <br><small class="text-muted">Represented on {{ last_pres.presentation.date|date:"Y-m-d" }}</small> {% endif %} {% endwith %} {% endif %} {% if check.compensation_info %} <br><small class="text-muted">{{ check.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('check', '{{ check.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=check.check_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="check" data-action="edit" data-id="{{ check.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="check" data-id="{{ check.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No checks found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- LCNs Tab Content --> <div class="tab-pane fade" id="lcns" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>LCN Number</th> <th>Issuing Bank</th> <th>Due Date</th> <th class="text-right" style="min-width: 120px;">Amount</th> <th>Bank Issued To</th> <th>Presentation</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for lcn in receipts.lcns %} <tr class="status-{{ lcn.status|lower }}"> <td>{{ lcn.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ lcn.entity.name }}</strong><br> <small class="text-muted">{{ lcn.entity.ice_code }}</small> </td> <td> <small>{{ lcn.client.name }}</small> </td> <td>{{ lcn.lcn_number }}</td> <td>{{ lcn.get_issuing_bank_display }}</td> <td>{{ lcn.due_date|date:"Y-m-d" }}</td> <td class="text-right" style="min-width: 120px;">{{ lcn.amount|format_balance }}</td> <!-- Bank Issued To column --> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ lcn.status|status_badge }}"> {{ lcn.get_status_display }} </span> {% if lcn.status == 'UNPAID' and lcn.rejection_cause %} <br><small class="text-danger">{{ lcn.get_rejection_cause_display }}</small> {% endif %} {% if lcn.compensation_info %} <br><small class="text-muted">{{ lcn.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('lcn', '{{ lcn.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=lcn.lcn_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="lcn" data-action="edit" data-id="{{ lcn.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="lcn" data-id="{{ lcn.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No LCNs found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Cash Tab --> <div class="tab-pane fade" id="cash" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>Reference</th> <th>Credited Account</th> <th class="text-right" style="min-width: 120px;">Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for cash in receipts.cash %} <tr> <td>{{ cash.operation_date|date:"Y-m-d" }}</td> <td>{{ cash.entity.name }}</td> <td>{{ cash.client.name }}</td> <td>{{ cash.reference_number }}</td> <td>{{ cash.credited_account.bank }} - {{ cash.credited_account.account_number }}</td> <td class="text-right" style="min-width: 120px;">{{ cash.amount|format_balance }}</td> <td> <div class="btn-group"> {% if cash.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="cash" data-action="edit" data-id="{{ cash.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if cash.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="cash" data-id="{{ cash.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </div> </td> </tr> {% empty %} <tr> <td colspan="6" class="text-center">No cash receipts found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Transfers Tab --> <div class="tab-pane fade" id="transfers" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>Transfer Reference</th> <th>Transfer Date</th> <th>Credited Account</th> <th class="text-right" style="min-width: 120px;">Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for transfer in receipts.transfers %} <tr> <td>{{ transfer.operation_date|date:"Y-m-d" }}</td> <td>{{ transfer.entity.name }}</td> <td>{{ transfer.client.name }}</td> <td>{{ transfer.transfer_reference }}</td> <td>{{ transfer.transfer_date|date:"Y-m-d" }}</td> <td>{{ transfer.credited_account.bank }} - {{ transfer.credited_account.account_number }}</td> <td class="text-right" style="min-width: 120px;">{{ transfer.amount|format_balance }}</td> <td> <div class="btn-group"> {% if transfer.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="transfer" data-action="edit" data-id="{{ transfer.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if transfer.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="transfer" data-id="{{ transfer.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </td> </tr> {% empty %} <tr> <td colspan="7" class="text-center">No transfers found</td> </tr> {% endfor %} </tbody> </table> </div> </div> </div> </div> </div> <!-- Receipt Modal --> <div class="modal fade" id="receiptModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Modal content will be loaded dynamically --> </div> </div> </div> <!-- Timeline Modal --> <div class="modal fade" id="timelineModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Content will be loaded dynamically --> </div> </div> </div> <style> /* Status Badge Colors */ .badge-portfolio { background-color: #6c757d; } .badge-presented_collection, .badge-presented_discount { background-color: #17a2b8; } .badge-paid { background-color: #28a745; } .badge-unpaid { background-color: #dc3545; } .badge-compensated { background-color: #fd7e14; } /* Orange color for compensated */ /* Row Status Highlighting */ tr.status-paid { background-color: rgba(40, 167, 69, 0.1); } /* Light green */ tr.status-unpaid { background-color: rgba(220, 53, 69, 0.1); } /* Light red */ tr.status-compensated { background-color: rgba(253, 126, 20, 0.1); } /* Light orange */ /* Maintain hover effect with status background */ .table-hover tbody tr:hover { background-color: rgba(0, 0, 0, 0.075) !important; } .form-floating > .form-control { padding-left: 2.5rem; } .form-floating > label { padding-left: 1.75rem; } /* Autocomplete dropdown styling */ .ui-autocomplete { max-height: 200px; overflow-y: auto; border-radius: 0.5rem; border: 1px solid rgba(0,0,0,.1); box-shadow: 0 0.5rem 1rem rgba(0,0,0,.15); z-index: 1050; } </style> <script> console.log("Extra JS loaded"); const MOROCCAN_BANKS = [ {% for code, name in bank_choices %} ['{{ code }}', '{{ name }}'], {% endfor %} ]; var bankAccountsList = [ {value: '', label: 'Select Bank Account'}, {% for account in bank_accounts %} { value: "{{ account.id }}", label: "{{ account.get_bank_display }} - {{ account.account_number }}" }{% if not forloop.last %},{% endif %} {% endfor %} ]; // Debug helper const debug = { log: function(component, message, data = null) { console.log(`[${component}]`, message, data || ''); } }; // Track filters per tab let activeFilters = null; // Handle tab switching $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) { debug.log('TabSwitch', 'Tab changed to:', e.target.id); // Get the target tab id (checks, lcns, cash, or transfers) const targetTab = $(e.target).attr('href').replace('#', ''); debug.log('TabSwitch', 'Target tab:', targetTab); // Clean up existing filters if any if (activeFilters) { debug.log('TabSwitch', 'Cleaning up old filters'); activeFilters.destroy(); activeFilters = null; } // Initialize new filters based on tab type debug.log('TabSwitch', 'Initializing filters for:', targetTab); activeFilters = new ReceiptFilters(targetTab, '/testapp/receipts/filter/?type=' + targetTab); }); $(document).ready(function() { // Initialize filters for each tab debug.log('Init', 'Initializing filters for active tab'); const activeTab = $('.tab-pane.active').attr('id'); debug.log('Init', 'Active tab:', activeTab); activeFilters = new ReceiptFilters(activeTab, '/testapp/receipts/filter/?type=' + activeTab); $('#receiptModal').on('show.bs.modal', function(e) { const button = $(e.relatedTarget); const type = button.data('type'); const action = button.data('action'); const id = button.data('id'); let url = ''; if (action === 'edit') { url += `edit/${type}/${id}/`; } else { url += `create/${type}/`; } // Load modal content $.get(url, function(data) { $('#receiptModal .modal-content').html(data); initializeForm(); if (action === 'edit') { // Set form action URL for edit $('#receiptForm').attr('action', url); // Initialize Select2 with pre-selected values if (data.client) { const clientOption = new Option(data.client.text, data.client.id, true, true); $('#client').append(clientOption).trigger('change'); } if (data.entity) { const entityOption = new Option(data.entity.text, data.entity.id, true, true); $('#entity').append(entityOption).trigger('change'); } } }); }); // Handle form submission for both create and edit $(document).on('submit', '#receiptForm', function(e) { e.preventDefault(); const form = $(this); // Create FormData object and append transfer fields manually let formData = new FormData(form[0]); if ($('#transfer_reference').length) { formData.append('transfer_reference', $('#transfer_reference').val()); formData.append('transfer_date', $('#transfer_date').val()); } // Convert FormData to URLSearchParams for jQuery const data = new URLSearchParams(formData).toString(); $.ajax({ url: form.attr('action'), type: 'POST', data: data, success: function(response) { if (response.status === 'success') { $('#receiptModal').modal('hide'); showToast(response.message, 'success'); location.reload(); } else { showFormErrors(form, response.errors); } }, error: function(xhr) { try { const errors = JSON.parse(xhr.responseText); showFormErrors(form, errors); } catch (e) { showToast('An error occurred while saving the receipt.', 'error'); } } }); }); function showFormErrors(form, errors) { // Clear previous errors form.find('.is-invalid').removeClass('is-invalid'); form.find('.invalid-feedback').remove(); // Show new errors Object.keys(errors).forEach(field => { const input = form.find(`[name="${field}"]`); const error = errors[field].join(' '); input.addClass('is-invalid'); input.after(`<div class="invalid-feedback">${error}</div>`); }); } function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">Notification</strong> <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> <div class="toast-body">${message}</div> </div> `; const toastContainer = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>'); toastContainer.html(toast); $('body').append(toastContainer); $('.toast').toast('show'); // Remove toast after it's hidden $('.toast').on('hidden.bs.toast', function() { $(this).closest('.toast-container').remove(); }); } }); // Initialize form elements after modal load function initializeForm() { console.log('Initializing form with autocomplete...'); console.log('Client input exists:', $('#client').length); console.log('Entity input exists:', $('#entity').length); // Initialize client autocomplete $("#client").autocomplete({ minLength: 0, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 0, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); console.log('XHR response:', xhr.responseText); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Add some basic styling to autocomplete dropdown $(".ui-autocomplete").addClass("dropdown-menu").css({ 'max-height': '200px', 'overflow-y': 'auto', 'overflow-x': 'hidden', 'z-index': '9999' }); } // Modify the modal show event handler $('#receiptModal').on('show.bs.modal', function(e) { const button = $(e.relatedTarget); const type = button.data('type'); const action = button.data('action'); const id = button.data('id'); let url = ''; if (action === 'edit') { url = `edit/${type}/${id}/`; } else { url = `create/${type}/`; } $.get(url, function(data) { $('#receiptModal .modal-content').html(data); initializeForm(); initializeBankAutocomplete(); // Add this line }); }); // Handle delete $('.delete-receipt').click(function() { if (confirm('Are you sure you want to delete this receipt?')) { const type = $(this).data('type'); const id = $(this).data('id'); $.ajax({ url: `/testapp/receipts/delete/${type}/${id}/`, type: 'POST', headers: { 'X-CSRFToken': '{{ csrf_token }}' }, success: function() { location.reload(); }, error: function() { alert('Error deleting receipt'); } }); } }); class ReceiptFilters { constructor(tabId, filterEndpoint) { debug.log('ReceiptFilters', 'Initializing for tab:', tabId); this.tab = $(`#${tabId}`); this.endpoint = filterEndpoint; this.currentFilters = {}; this.type = tabId; // 'checks', 'lcns', 'cash', 'transfers' this.createFilterUI(); this.initializeFilters(); } getFilterConfig() { debug.log('ReceiptFilters', 'Getting filter config for type:', this.type); const banksList = [ {value: '', label: 'All banks'}, {% for code, name in bank_choices %} { label: '{{ name }}', value: '{{ code }}', display: '{{ name }}' }, {% endfor %} ]; const configs = { 'checks': [ { type: 'client', icon: 'user', label: 'Client', col: 3 }, { type: 'entity', icon: 'building', label: 'Entity', col: 3 }, { type: 'status', icon: 'tag', label: 'Status', col: 3, isSelect: true, options: [ {value: '', label: 'All Statuses'}, {value: 'PORTFOLIO', label: 'In Portfolio'}, {value: 'PRESENTED_COLLECTION', label: 'Presented for Collection'}, {value: 'PRESENTED_DISCOUNT', label: 'Presented for Discount'}, {value: 'DISCOUNTED', label: 'Discounted'}, {value: 'PAID', label: 'Paid'}, {value: 'UNPAID', label: 'Unpaid'}, {value: 'COMPENSATED', label: 'Compensated'} ] }, { type: 'number', icon: 'hashtag', label: 'Check Number', col: 3 }, // Add issuing bank dropdown { type: 'issuing_bank', icon: 'university', label: 'Issuing Bank', col: 4, isSelect: true, options: banksList }, // Add bank issued to dropdown { type: 'bank_issued_to', icon: 'university', label: 'Bank Issued To', col: 4, isSelect: true, options: bankAccountsList }, // Add date ranges { type: 'creation_date_from', icon: 'calendar', label: 'Creation Date From', col: 4, isDate: true }, { type: 'creation_date_to', icon: 'calendar', label: 'Creation Date To', col: 4, isDate: true }, { type: 'due_date_from', icon: 'calendar', label: 'Due Date From', col: 4, isDate: true }, { type: 'due_date_to', icon: 'calendar', label: 'Due Date To', col: 4, isDate: true }, // Add amount ranges { type: 'amount_from', icon: 'money-bill', label: 'Amount From', col: 4, isNumber: true }, { type: 'amount_to', icon: 'money-bill', label: 'Amount To', col: 4, isNumber: true }, { type: 'historical_status', icon: 'history', label: 'Was Status', col: 4, isSelect: true, options: [ {value: '', label: 'All Statuses'}, {value: 'PORTFOLIO', label: 'In Portfolio'}, {value: 'PRESENTED_COLLECTION', label: 'Presented for Collection'}, {value: 'PRESENTED_DISCOUNT', label: 'Presented for Discount'}, {value: 'PAID', label: 'Paid'}, {value: 'REJECTED', label: 'Rejected'}, {value: 'COMPENSATED', label: 'Compensated'}, {value: 'UNPAID', label: 'Unpaid'} ] } ], 'lcns': [ { type: 'client', icon: 'user', label: 'Client', col: 3 }, { type: 'entity', icon: 'building', label: 'Entity', col: 3 }, { type: 'status', icon: 'tag', label: 'Status', col: 3, isSelect: true, options: [ {value: '', label: 'All Statuses'}, {value: 'PORTFOLIO', label: 'In Portfolio'}, {value: 'PRESENTED_COLLECTION', label: 'Presented for Collection'}, {value: 'PRESENTED_DISCOUNT', label: 'Presented for Discount'}, {value: 'DISCOUNTED', label: 'Discounted'}, {value: 'PAID', label: 'Paid'}, {value: 'UNPAID', label: 'Unpaid'}, {value: 'COMPENSATED', label: 'Compensated'} ] }, { type: 'number', icon: 'hashtag', label: 'LCN Number', col: 3 }, // Add issuing bank dropdown { type: 'issuing_bank', icon: 'university', label: 'Issuing Bank', col: 4, isSelect: true, options: banksList }, { type: 'bank_issued_to', icon: 'university', label: 'Bank Issued To', col: 4, isSelect: true, options: bankAccountsList }, { type: 'creation_date_from', icon: 'calendar', label: 'Creation Date From', col: 4, isDate: true }, { type: 'creation_date_to', icon: 'calendar', label: 'Creation Date To', col: 4, isDate: true }, { type: 'due_date_from', icon: 'calendar', label: 'Due Date From', col: 4, isDate: true }, { type: 'due_date_to', icon: 'calendar', label: 'Due Date To', col: 4, isDate: true }, { type: 'amount_from', icon: 'money-bill', label: 'Amount From', col: 4, isNumber: true }, { type: 'amount_to', icon: 'money-bill', label: 'Amount To', col: 4, isNumber: true }, { type: 'historical_status', icon: 'history', label: 'Was Status', col: 4, isSelect: true, options: [ {value: '', label: 'All Statuses'}, {value: 'PORTFOLIO', label: 'In Portfolio'}, {value: 'PRESENTED_COLLECTION', label: 'Presented for Collection'}, {value: 'PRESENTED_DISCOUNT', label: 'Presented for Discount'}, {value: 'PAID', label: 'Paid'}, {value: 'REJECTED', label: 'Rejected'}, {value: 'COMPENSATED', label: 'Compensated'}, {value: 'UNPAID', label: 'Unpaid'} ] } ], 'cash': [ { type: 'client', icon: 'user', label: 'Client', col: 4 }, { type: 'entity', icon: 'building', label: 'Entity', col: 4 }, { type: 'credited_account', icon: 'university', label: 'Credited Account', col: 4, isSelect: true, options: bankAccountsList } ], 'transfers': [ { type: 'client', icon: 'user', label: 'Client', col: 4 }, { type: 'entity', icon: 'building', label: 'Entity', col: 4 }, { type: 'credited_account', icon: 'university', label: 'Credited Account', col: 4, isSelect: true, options: bankAccountsList } ] }; const config = configs[this.type]; debug.log('ReceiptFilters', 'Filter config:', config); return config || []; } createFilterUI() { debug.log('ReceiptFilters', 'Creating filter UI'); const filters = this.getFilterConfig(); let filterElements = []; filters.forEach(filter => { filterElements.push(this.createFilterElement(filter)); }); const filterHtml = ` <div class="card mb-4" id="${this.type}-filters"> <div class="card-header d-flex justify-content-between align-items-center bg-light"> <h6 class="mb-0">Filters</h6> <div class="btn-group"> <button type="button" class="btn btn-outline-secondary btn-sm" id="${this.type}-reset-filters"> <i class="fas fa-undo me-1"></i>Reset </button> <button type="button" class="btn btn-outline-primary btn-sm toggle-filters"> <i class="fas fa-filter me-1"></i>Show Filters </button> </div> </div> <div class="card-body filter-content" style="display: none;"> <div class="row g-3"> ${filterElements.join('')} </div> </div> </div>`; this.tab.find('.table-responsive').before(filterHtml); // Set up toggle button $(`#${this.type}-filters .toggle-filters`).click(() => { const $content = $(`#${this.type}-filters .filter-content`); const $button = $(`#${this.type}-filters .toggle-filters`); $content.slideToggle(500, () => { $button.html( $content.is(':visible') ? '<i class="fas fa-filter me-1"></i>Hide Filters' : '<i class="fas fa-filter me-1"></i>Show Filters' ); }); }); // Set up reset button $(`#${this.type}-reset-filters`).click(() => { this.resetFilters(); }); } // Add resetFilters method to your class resetFilters() { debug.log('ReceiptFilters', 'Resetting all filters'); // Reset all inputs and selects const filters = this.getFilterConfig(); filters.forEach(filter => { const $element = $(`#${this.type}-${filter.type}-filter`); if ($element.is('select')) { $element.val('').trigger('change'); } else { $element.val('').trigger('blur'); } }); // Clear current filters this.currentFilters = {}; this.applyFilters(); } createFilterElement(filter) { debug.log('Creating filter element:', filter); if (filter.isSelect) { return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <select class="form-control" id="${this.type}-${filter.type}-filter"> ${filter.options.map(opt => ` <option value="${opt.value}">${opt.label}</option> `).join('')} </select> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } else if (filter.isDate) { return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <input type="date" class="form-control" id="${this.type}-${filter.type}-filter"> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } else if (filter.isNumber) { return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <input type="number" step="0.01" class="form-control" id="${this.type}-${filter.type}-filter"> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } // Default text input return ` <div class="col-md-${filter.col}"> <div class="form-floating"> <input type="text" class="form-control" id="${this.type}-${filter.type}-filter"> <label> <i class="fas fa-${filter.icon} text-primary me-2"></i>${filter.label} </label> </div> </div>`; } initializeFilters() { debug.log('ReceiptFilters', 'Initializing filter handlers'); const filters = this.getFilterConfig(); filters.forEach(filter => { const elementId = `#${this.type}-${filter.type}-filter`; debug.log('Processing filter:', { type: filter.type, elementId: elementId, elementExists: $(elementId).length > 0, isSelect: filter.isSelect, isDate: filter.isDate, isNumber: filter.isNumber }); if (filter.type === 'client') { this.initializeClientAutocomplete(); $(elementId).on('blur', () => { if (!$(elementId).val()) { debug.log('Filter', 'Client input emptied on blur'); this.updateFilter('client', ''); } }); } else if (filter.type === 'entity') { this.initializeEntityAutocomplete(); $(elementId).on('blur', () => { if (!$(elementId).val()) { debug.log('Filter', 'Entity input emptied on blur'); this.updateFilter('entity', ''); } }); } else if (filter.isSelect || filter.isDate || filter.isNumber) { debug.log('Setting up select/date/number filter:', filter.type); $(elementId).on('change', () => { const value = $(elementId).val(); debug.log('Filter', `${filter.type} changed:`, value); this.updateFilter(filter.type, value); }); // Blur handler for date and number inputs if (filter.isDate || filter.isNumber) { debug.log('Adding blur handler for:', filter.type); $(elementId).on('blur', () => { if (!$(elementId).val()) { debug.log('Filter', `${filter.type} input emptied on blur`); this.updateFilter(filter.type, ''); } }); } } else { let timeout; $(elementId).on('input', (e) => { clearTimeout(timeout); timeout = setTimeout(() => { debug.log('Filter', `${filter.type} input:`, e.target.value); this.updateFilter(filter.type, e.target.value); }, 300); }); $(elementId).on('blur', (e) => { if (!e.target.value) { debug.log('Filter', `${filter.type} input emptied on blur`); this.updateFilter(filter.type, ''); } }); } }); if (this.type === 'cash' || this.type === 'transfers') { const creditedAccountId = `#${this.type}-credited_account-filter`; debug.log('Filter', 'Initializing credited account select:', creditedAccountId); $(creditedAccountId).on('change', () => { const value = $(creditedAccountId).val(); debug.log('Filter', 'Credited account changed:', value); this.updateFilter('credited_account', value); }); } } initializeClientAutocomplete() { debug.log('ReceiptFilters', 'Initializing client autocomplete'); $(`#${this.type}-client-filter`).autocomplete({ minLength: 0, source: (request, response) => { $.get('/testapp/client/autocomplete', { term: request.term }).done(data => { debug.log('Autocomplete', 'Client results:', data); response(data.results.map(item => ({ label: item.text, value: item.id }))); }); }, select: (event, ui) => { debug.log('Autocomplete', 'Client selected:', ui.item); $(`#${this.type}-client-filter`).val(ui.item.label); this.updateFilter('client', ui.item.value); return false; } }); } initializeEntityAutocomplete() { debug.log('ReceiptFilters', 'Initializing entity autocomplete'); $(`#${this.type}-entity-filter`).autocomplete({ minLength: 0, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: (event, ui) => { console.log('Entity selected:', ui.item); $(`#${this.type}-entity-filter`).val(ui.item.label); this.updateFilter('entity', ui.item.value); return false; } }); } updateFilter(type, value) { debug.log('Filter', `Updating ${type} filter with value:`, value); // Handle empty values correctly if (value === '' || value === null || value === undefined) { debug.log('Filter', `Removing ${type} filter due to empty value`); delete this.currentFilters[type]; } else { debug.log('Filter', `Setting ${type} filter to:`, value); this.currentFilters[type] = value; } // Debugging for current filters state debug.log('Filter', 'Current filters state:', this.currentFilters); // Apply filters immediately this.applyFilters(); } applyFilters() { debug.log('ReceiptFilters', 'Applying filters:', this.currentFilters); $.get(this.endpoint, this.currentFilters) .done(response => { debug.log('ReceiptFilters', 'Filter response received'); this.tab.find('tbody').html(response.html); }) .fail(error => { console.error('Filter error:', error); }); } destroy() { debug.log('ReceiptFilters', 'Destroying filters'); // Remove filter UI $(`#${this.type}-filters`).remove(); // Clean up event handlers const filters = this.getFilterConfig(); filters.forEach(filter => { const elementId = `#${this.type}-${filter.type}-filter`; $(elementId).off(); if (filter.type === 'client' || filter.type === 'entity') { $(elementId).autocomplete('destroy'); } }); } } // Keyboard shortcuts $(document).keydown(function(e) { // Only trigger if no modal is open and no input is focused if ($('.modal:visible').length === 0 && !$(document.activeElement).is('input, textarea, select')) { let receiptType = null; if (e.altKey) { switch(e.key.toLowerCase()) { case 'c': // Alt + C for Check receiptType = 'check'; break; case 'l': // Alt + L for LCN receiptType = 'lcn'; break; case 'e': // Alt + M for Cash (Money) receiptType = 'cash'; break; case 'v': // Alt + T for Transfer receiptType = 'transfer'; break; } if (receiptType) { e.preventDefault(); const url = "{% url 'receipt-create' 'TYPE' %}".replace('TYPE', receiptType); const modal = $('#receiptModal'); modal.modal('show'); modal.find('.modal-content').load(url, function() { setTimeout(function() { initializeForm(); }, 100); }); } } } }); // Handle presentation status update function updatePresentation(id) { const bankRef = $('#bankReference').val(); if (!bankRef) { showError('Bank reference is required'); return; } $.ajax({ url: `/testapp/presentations/${id}/edit/`, method: 'POST', contentType: 'application/json', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, data: JSON.stringify({ bank_reference: bankRef, status: $('#presentationStatus').val() }), success: () => location.reload(), error: xhr => showError(xhr.responseJSON?.message || 'Update failed') }); } // Handle receipt status update $(document).on('change', '.receipt-status', function() { const $select = $(this); const receiptId = $select.data('receipt-id'); const newStatus = $select.val(); if (!confirm('This status change is irreversible. Continue?')) { $select.val($select.find('option').not(':selected').val()); return; } $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', contentType: 'application/json', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, data: JSON.stringify({ receipt_id: receiptId, receipt_status: newStatus }), success: () => { $select.prop('disabled', true); location.reload(); }, error: xhr => { showError(xhr.responseJSON?.message || 'Status update failed'); $select.val($select.find('option').not(':selected').val()); } }); }); function viewReceiptTimeline(receiptType, receiptId) { console.log(`Loading timeline for ${receiptType} ${receiptId}`); // Show loading state in modal $('#timelineModal').modal('show'); $('#timelineModal .modal-content').html(` <div class="modal-body text-center"> <div class="spinner-border text-primary" role="status"> <span class="sr-only">Loading...</span> </div> <p class="mt-2">Loading timeline...</p> </div> `); // Load timeline content $.ajax({ url: `/testapp/receipts/${receiptType}/${receiptId}/timeline/`, method: 'GET', success: function(response) { $('#timelineModal .modal-content').html(response); // Initialize any tooltips or popovers $('#timelineModal [data-toggle="tooltip"]').tooltip(); $('#timelineModal [data-toggle="popover"]').popover(); // Add animation classes to timeline items $('.timeline-item').each(function(index) { $(this) .addClass('animate__animated animate__fadeInLeft') .css('animation-delay', `${index * 0.1}s`); }); }, error: function(xhr) { let errorMessage = 'Failed to load timeline'; try { const response = JSON.parse(xhr.responseText); errorMessage = response.message || errorMessage; } catch(e) {} $('#timelineModal .modal-content').html(` <div class="modal-header"> <h5 class="modal-title">Error</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="alert alert-danger"> ${errorMessage} </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> </div> `); } }); } // Optional: Add helper function for formatting dates in timeline function formatTimelineDate(dateString) { const date = new Date(dateString); return new Intl.DateTimeFormat('fr-MA', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date); } // Add modal cleanup on hide $('#timelineModal').on('hidden.bs.modal', function() { $(this).find('.modal-content').html(''); }); // Optional: Add keyboard shortcut to close modal $(document).keydown(function(e) { if (e.key === 'Escape' && $('#timelineModal').hasClass('show')) { $('#timelineModal').modal('hide'); } }); function showError(message) { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-danger text-white"> <strong class="mr-auto">Error</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } // Add tooltip hints for shortcuts $('[data-toggle="modal"][data-target="#receiptModal"]').each(function() { const type = $(this).data('type'); let shortcut = ''; switch(type) { case 'check': shortcut = 'Alt+C'; break; case 'lcn': shortcut = 'Alt+L'; break; case 'cash': shortcut = 'Alt+M'; break; case 'transfer': shortcut = 'Alt+T'; break; } if (shortcut) { $(this).attr('title', `${$(this).text().trim()} (${shortcut})`); } }); </script> {% endblock %}
```

# templates/receipt/receipt_timeline_modal.html

```html
{% load accounting_filters %} <!-- templates/receipt/receipt_timeline_modal.html --> <div class="modal-header"> <h5 class="modal-title"> {% if receipt.check_number %} <i class="fas fa-money-check me-2"></i>Check #{{ receipt.check_number }} {% else %} <i class="fas fa-file-invoice-dollar me-2"></i>LCN #{{ receipt.lcn_number }} {% endif %} History </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Receipt Summary --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <p><strong>Entity:</strong> {{ receipt.entity.name }}</p> <p><strong>Client:</strong> {{ receipt.client.name }}</p> <p><strong>Amount:</strong> {{ receipt.amount|format_balance }}</p> </div> <div class="col-md-6"> <p><strong>Status:</strong> <span class="badge badge-{{ receipt.status|lower }}"> {{ receipt.get_status_display }} </span> </p> <p><strong>Created:</strong> {{ receipt.created_at|date:"d/m/Y H:i" }}</p> <p><strong>Due Date:</strong> {{ receipt.due_date|date:"d/m/Y" }}</p> </div> </div> </div> </div> <!-- Timeline --> <div class="timeline"> {% for event in history %} <div class="timeline-item"> <div class="timeline-marker {% if event.action == 'status_changed' %}bg-primary {% elif event.action == 'presented' %}bg-info {% elif event.action == 'compensated' %}bg-warning {% elif event.action == 'compensation_paid' %}bg-success {% else %}bg-secondary{% endif %}"> </div> <div class="timeline-content"> <div class="d-flex justify-content-between"> <h6 class="mb-0">{{ event.get_action_display }}</h6> <small class="text-muted"> {{ event.business_date|default:event.timestamp|date:"d/m/Y H:i" }} {% if event.business_date %} <br><span class="text-secondary">(Recorded: {{ event.timestamp|date:"d/m/Y H:i" }})</span> {% endif %} </small> </div> <p class="mb-0">{{ event.notes }}</p> {% if event.action == 'status_changed' %} <small class="text-muted"> Changed from <span class="badge badge-{{ event.old_value.status|lower }}"> {{ event.old_value.status|default_if_none:""|get_status_display }} </span> to <span class="badge badge-{{ event.new_value.status|lower }}"> {{ event.new_value.status|default_if_none:""|get_status_display }} </span> </small> {% endif %} {% if event.user %} <small class="text-muted d-block">by {{ event.user.get_full_name|default:event.user.username }}</small> {% endif %} </div> </div> {% empty %} <p class="text-center text-muted">No history available</p> {% endfor %} </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> </div> <style> .timeline { position: relative; padding-left: 3rem; margin-bottom: 3rem; } .timeline::before { content: ''; position: absolute; left: 11px; top: 0; height: 100%; width: 2px; background-color: #e9ecef; } .timeline-item { position: relative; margin-bottom: 2rem; } .timeline-marker { position: absolute; left: -3rem; width: 24px; height: 24px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 2px #e9ecef; } .timeline-content { background: #f8f9fa; border-radius: 0.3rem; padding: 1rem; position: relative; } .timeline-content::before { content: ''; position: absolute; left: -0.5rem; top: 0.75rem; width: 0.5rem; height: 0.5rem; background: inherit; transform: rotate(45deg); } /* Status Badge Colors */ .badge-portfolio { background-color: #6c757d; color: white; } .badge-presented { background-color: #17a2b8; color: white; } .badge-presented_discount { background-color: #e437d3; color: white; } .badge-paid { background-color: #28a745; color: white; } .badge-discounted { background-color: #1032dc; color: white; } .badge-unpaid { background-color: #dc3545; color: white; } .badge-compensated { background-color: #fd7e14; color: white; } </style>
```

# templatetags/__init__.py

```py

```

# templatetags/accounting_filters.py

```py
from django import template
from django.template.defaultfilters import floatformat
from decimal import InvalidOperation, Decimal


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

@register.filter
def format_balance(value):
    """
    Formats a balance number without negative sign
    """
    if value is None:
        return ''
    
    try:
        # Convert string to Decimal if needed
        if isinstance(value, str):
            value = Decimal(value)
        
        # Now we can safely use abs()
        formatted = floatformat(abs(value), 2)
        
        # Add space thousand separators
        int_part, dec_part = formatted.split('.')
        int_with_spaces = ''
        for i, digit in enumerate(reversed(int_part)):
            if i and i % 3 == 0:
                int_with_spaces = ' ' + int_with_spaces
            int_with_spaces = digit + int_with_spaces
            
        return f'{int_with_spaces}.{dec_part}'
        
    except (TypeError, ValueError, InvalidOperation) as e:
        print(f"Error formatting balance: {e}, value: {value}, type: {type(value)}")
        return str(value)

@register.filter
def get_status_display(status_code):
    STATUS_DISPLAY = {
        'PORTFOLIO': 'In Portfolio',
        'PRESENTED_COLLECTION': 'Presented for Collection',
        'PRESENTED_DISCOUNT': 'Presented for Discount',
        'DISCOUNTED': 'Discounted',
        'PAID': 'Paid',
        'REJECTED': 'Rejected',
        'COMPENSATED': 'Compensated',
        'UNPAID': 'Unpaid'
    }
    return STATUS_DISPLAY.get(status_code, status_code)

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return value
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
        'cancelled': 'danger',
        'unpaid': 'danger'
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

@register.filter
def status_badge(status):
    """
    Convert status to a bootstrap badge class
    """
    status_map = {
        'pending': 'badge-secondary',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'in_progress': 'badge-warning',
        'completed': 'badge-primary'
    }
    return status_map.get(status, 'badge-light')

```

# templatetags/presentation_filters.py

```py
from django import template
import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.filter
def status_badge(status):
    """Returns appropriate badge class for presentation status"""
    # Convert status to lowercase for consistent mapping
    original_status = str(status)
    status = original_status.lower()
    
    logger.debug(f"status_badge filter called with original status: {original_status}")
    
    result = {
        'pending': 'secondary',
        'presented': 'info',
        'paid': 'success',
        'rejected': 'danger',
        'unpaid': 'danger',
        'portfolio': 'primary',
        'presented_collection': 'info',
        'presented_discount': 'info',
        'discounted': 'success',
        
        # Explicitly map uppercase statuses
        'UNPAID': 'danger',
        'PAID': 'success',
        'REJECTED': 'danger',
        'PRESENTED_COLLECTION': 'info',
        'PRESENTED_DISCOUNT': 'info',
        'DISCOUNTED': 'success',
    }.get(original_status, status)  # Try original status first, then fallback to lowercase
    
    logger.debug(f"Returning badge class: {result}")
    return result
```

# templatetags/receipt_filters.py

```py
from django import template

register = template.Library()

@register.filter
def get_status_display(status_code):
    STATUS_DISPLAY = {
        'PORTFOLIO': 'In Portfolio',
        'PRESENTED_COLLECTION': 'Presented for Collection',
        'PRESENTED_DISCOUNT': 'Presented for Discount',
        'DISCOUNTED': 'Discounted',
        'PAID': 'Paid',
        'REJECTED': 'Rejected',
        'COMPENSATED': 'Compensated',
        'UNPAID': 'Unpaid'
    }
    return STATUS_DISPLAY.get(status_code, status_code)
```

# templatetags/status_filters.py

```py
from django import template

register = template.Library()

@register.filter
def status_badge(status):
    """Returns appropriate badge class for receipt status"""
    status = str(status).lower()
    
    return {
        'portfolio': 'secondary',
        'presented_collection': 'info',
        'presented_discount': 'info',
        'discounted': 'success',
        'paid': 'success',
        'unpaid': 'danger',
        'rejected': 'danger',
        'compensated': 'warning'
    }.get(status, 'secondary')
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

from .views_bank import (
    BankAccountListView, BankAccountCreateView, 
    BankAccountDeactivateView, BankAccountFilterView, BankAccountUpdateView, BankAccountDeleteView,
    bank_account_autocomplete, BankFeeCreateView, BankFeeDeleteView, PresentationAutocompleteView
)

from .views_receipts import (
    ReceiptListView, ReceiptCreateView, ReceiptUpdateView, ReceiptDeleteView, ReceiptDetailView, client_autocomplete,
    entity_autocomplete, unpaid_receipt_autocomplete, ReceiptStatusUpdateView, UnpaidReceiptsView, ReceiptTimelineView,
    ReceiptFilterView)

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
    PresentationListView, PresentationCreateView, PresentationUpdateView, PresentationDeleteView,
    PresentationDetailView, AvailableReceiptsView, DiscountInfoView, PresentationFilterView
)

from .views_statement import (
    BankStatementView, AccountingView, OtherOperationsView
)

from .views_transfer import (
    CreateTransferView, DeleteTransferView
)


urlpatterns = [


    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/create/', BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<uuid:pk>/edit/', BankAccountUpdateView.as_view(), name='bank-account-edit'),
    path('bank-accounts/<uuid:pk>/delete/', BankAccountDeleteView.as_view(), name='bank-account-delete'),
    path('bank-accounts/<uuid:pk>/deactivate/', 
         BankAccountDeactivateView.as_view(), name='bank-account-deactivate'),
    path('bank-accounts/filter/', 
         BankAccountFilterView.as_view(), name='bank-account-filter'),
    path('bank-accounts/', bank_account_autocomplete, name='bank_account_autocomplete'),

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
    path('receipts/unpaid/autocomplete', unpaid_receipt_autocomplete, name='unpaid-receipt-autocomplete'),

    # Filter receipts
    path('receipts/filter/', ReceiptFilterView.as_view(), name='receipt-filter'),

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


    

]


```

# views_bank.py

```py
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import BankAccount, BankFeeTransaction, Presentation
from django.contrib import messages
import json
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.db.models import Q

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

        for account in queryset:
            account.current_balance = account.get_current_balance()
            
        return queryset

class BankAccountCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    data[field] = Decimal(str(data[field]))
                else:
                    data[field] = None
            
            # Create bank account
            account = BankAccount.objects.create(
                bank=data['bank'],
                account_number=data['account_number'],
                accounting_number=data['accounting_number'],
                journal_number=data['journal_number'],
                city=data['city'],
                account_type=data['account_type'],
                is_active=data.get('is_active', True),
                is_current=data.get('is_current', False),
                bank_overdraft=data['bank_overdraft'],
                overdraft_fee=data['overdraft_fee'],
                has_check_discount_line=data.get('has_check_discount_line', False),
                check_discount_line_amount=data['check_discount_line_amount'],
                has_lcn_discount_line=data.get('has_lcn_discount_line', False),
                lcn_discount_line_amount=data['lcn_discount_line_amount'],
                stamp_fee_per_receipt=data['stamp_fee_per_receipt']
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account created successfully',
                'id': str(account.id)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountUpdateView(View):
    def get(self, request, pk):
        account = get_object_or_404(BankAccount, pk=pk)
        return JsonResponse({
            'id': str(account.id),
            'bank': account.bank,
            'account_number': account.account_number,
            'accounting_number': account.accounting_number,
            'journal_number': account.journal_number,
            'city': account.city,
            'account_type': account.account_type,
            'is_active': account.is_active,
            'is_current': account.is_current,
            'bank_overdraft': str(account.bank_overdraft) if account.bank_overdraft else None,
            'overdraft_fee': str(account.overdraft_fee) if account.overdraft_fee else None,
            'has_check_discount_line': account.has_check_discount_line,
            'check_discount_line_amount': str(account.check_discount_line_amount) if account.check_discount_line_amount else None,
            'has_lcn_discount_line': account.has_lcn_discount_line,
            'lcn_discount_line_amount': str(account.lcn_discount_line_amount) if account.lcn_discount_line_amount else None,
            'stamp_fee_per_receipt': str(account.stamp_fee_per_receipt) if account.stamp_fee_per_receipt else None
        })

    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    setattr(account, field, Decimal(str(data[field])))
                else:
                    setattr(account, field, None)
            
            # Update other fields
            account.bank = data['bank']
            account.account_number = data['account_number']
            account.accounting_number = data['accounting_number']
            account.journal_number = data['journal_number']
            account.city = data['city']
            account.account_type = data['account_type']
            account.is_active = data.get('is_active', True)
            account.is_current = data.get('is_current', False)
            account.has_check_discount_line = data.get('has_check_discount_line', False)
            account.has_lcn_discount_line = data.get('has_lcn_discount_line', False)
            
            account.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountDeleteView(View):
    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            account.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

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

class BankFeeCreateView(View):
    """Handle creation of bank fee transactions"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create fee transaction
                fee = BankFeeTransaction.objects.create(
                    bank_account_id=data['bank_account'],
                    fee_type_id=data['fee_type'],
                    date=data['date'],
                    related_presentation_id=data.get('related_presentation'),
                    raw_amount=Decimal(str(data['raw_amount'])),
                    vat_rate=Decimal(str(data['vat_rate'])) if data['vat_rate'] else None,
                    vat_included=data['vat_included'],
                    vat_amount=Decimal(str(data.get('vat_amount', '0.00'))),
                    total_amount=Decimal(str(data.get('total_amount', '0.00')))
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Bank fee recorded successfully',
                    'id': str(fee.id)
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankFeeDeleteView(View):
    """Handle deletion of bank fee transactions"""
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                fee = get_object_or_404(BankFeeTransaction, pk=pk)
                fee.delete()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Bank fee deleted successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PresentationAutocompleteView(View):
    """Autocomplete for presentation references"""
    
    def get(self, request):
        try:
            term = request.GET.get('term', '')
            presentations = Presentation.objects.filter(
                Q(bank_reference__icontains=term) |
                Q(id__icontains=term)
            ).order_by('-date')[:10]
            
            results = [{
                'id': str(pres.id),
                'text': f"{pres.bank_reference or f'Pres. #{pres.id}'} ({pres.date})"
            } for pres in presentations]
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
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
from decimal import Decimal

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
            notes=data.get('notes', ''),
            sale_type=data['sale_type']
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

        # Calculate period totals (excluding previous balance)
        period_debit = Decimal('0.00')
        period_credit = Decimal('0.00')
        previous_balance = Decimal('0.00')

        for t in transactions:
            if t['type'] == 'BALANCE':
                previous_balance = t['balance']
            else:
                if t['debit']:
                    period_debit += t['debit']
                if t['credit']:
                    period_credit += t['credit']

        context.update({
            'transactions': transactions,
            'selected_year': year,
            'selected_month': month,
            'years': range(2024, timezone.now().year + 1),
            'months': [
                (i, calendar.month_name[i]) 
                for i in range(1, 13)
            ],
            'previous_balance': previous_balance,
            'period_debit': period_debit,
            'period_credit': period_credit,
            'final_balance': period_debit - period_credit + previous_balance
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

# views_presentation.py

```py
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from .models import Presentation, PresentationReceipt, CheckReceipt, LCN, BankAccount, ReceiptHistory, MOROCCAN_BANKS
from django.contrib.contenttypes.models import ContentType
import json
import traceback
from decimal import Decimal
from django.utils import timezone

class PresentationListView(ListView):
    """
    Display a list of all presentations with filtering capabilities.
    """
    model = Presentation
    template_name = 'presentation/presentation_list.html'
    context_object_name = 'presentations'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add bank accounts for the filter dropdown
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True)
        context['bank_choices'] = MOROCCAN_BANKS
        
        print("Debug - Context data:")
        print(f"Bank accounts: {[f'{acc.bank} - {acc.account_number}' for acc in context['bank_accounts']]}")
        return context

@method_decorator(csrf_exempt, name='dispatch')
class PresentationCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            print("Parsed JSON data:", data)

            with transaction.atomic():
                # Create the presentation
                presentation = Presentation.objects.create(
                    presentation_type=data['presentation_type'],
                    date=data['date'],
                    bank_account_id=data['bank_account'],
                    notes=data.get('notes', '')
                )
                print("Created presentation:", presentation)

                # Add receipts to the presentation
                receipt_type = data['receipt_type']
                receipt_ids = data['receipt_ids']
                print(f"Adding {receipt_type} receipts:", receipt_ids)

                for receipt_id in receipt_ids:
                    try:
                        # Get the correct receipt model
                        ReceiptModel = CheckReceipt if receipt_type == 'check' else LCN
                        receipt = ReceiptModel.objects.get(id=receipt_id)
                        
                        print(f"Processing receipt: {receipt}, Status: {receipt.status}")

                        # Verify receipt is in portfolio status
                        if receipt.status != 'PORTFOLIO' and receipt.status != 'UNPAID':
                            raise ValidationError(f"Receipt {receipt} is not in portfolio status")

                        # Create presentation receipt with proper field name
                        field_name = 'checkreceipt' if receipt_type == 'check' else 'lcn'
                        kwargs = {
                            'presentation': presentation,
                            'checkreceipt' if receipt_type == 'check' else 'lcn': receipt,
                            'amount': receipt.amount
                        }
                        
                        print(f"Creating presentation receipt with kwargs:", kwargs)
                        presentation_receipt = PresentationReceipt.objects.create(**kwargs)
                        receipt.bank_account = BankAccount.objects.get(id=data['bank_account'])
                        receipt.save()
                        print(f"Created presentation receipt: {presentation_receipt}")

                    except Exception as e:
                        import traceback
                        traceback.print_exc()

                        print(f"Error processing receipt {receipt_id}: {str(e)}")
                        raise

            return JsonResponse({
                'status': 'success',
                'message': 'Presentation created successfully',
                'id': str(presentation.id)
            })

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Error in presentation creation: {type(e).__name__} - {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Failed to create presentation: {str(e)}"
            }, status=400)

class PresentationDetailView(View):
    def get(self, request, pk):
        print("\n=== Starting PresentationDetailView.get ===")
        try:
            print(f"Looking for presentation with pk: {pk}")
            presentation = get_object_or_404(Presentation, pk=pk)
            print(f"Found presentation: {presentation}")
            
            print("Fetching related receipts...")
            receipts = presentation.presentation_receipts.all().select_related(
                'checkreceipt__client',
                'lcn__client',
                'checkreceipt__bank_account',
                'lcn__bank_account'
            )
            print(f"Found {receipts.count()} receipts")

            # Debug template loading
            print("\nChecking template tags:")
            from django.template import engines
            django_engine = engines['django']
            try:
                print("Available template tag libraries:", django_engine.template_libraries)
            except Exception as e:
                print(f"Error accessing template libraries: {e}")

            context = {
                'presentation': presentation,
                'receipts': receipts,
                'rejection_causes': CheckReceipt.REJECTION_CAUSES,
                'total_amount': sum(receipt.amount for receipt in receipts)
            }
            print("\nContext prepared:", context)
            
            try:
                print("\nAttempting to render template...")
                rendered = render(
                    request, 
                    'presentation/presentation_detail_modal.html',
                    context
                )
                print("Template rendered successfully")
                return rendered
            except Exception as template_error:
                import traceback
                print("\nTemplate rendering error:")
                print(traceback.format_exc())
                raise template_error

        except Exception as e:
            import traceback
            print("\n=== Error in PresentationDetailView ===")
            print(traceback.format_exc())
            print("=======================================")
            return JsonResponse({
                'status': 'error',
                'message': f"Detail view error: {str(e)}",
                'traceback': traceback.format_exc()
            }, status=400)

def handle_receipt_status(receipt, new_status):
        if new_status == 'paid':
            receipt.status = 'PAID'
        elif new_status == 'unpaid':
            receipt.status = 'UNPAID'
        receipt.save()

@method_decorator(csrf_exempt, name='dispatch')
class PresentationUpdateView(View):
    def post(self, request, pk):
        print("\n=== Starting presentation edit ===")
        try:
            data = json.loads(request.body)
            print(f"Parsed data: {data}")
            print(f"Request headers: {dict(request.headers)}")
            
            with transaction.atomic():
                presentation = get_object_or_404(Presentation, pk=pk)
                print(f"Found presentation: {presentation.__dict__}")

                if presentation.status == 'pending':
                    # Handle initial status change
                    if not data.get('bank_reference'):
                        print("Error: Missing bank reference")
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Bank reference is required'
                        }, status=400)
                    
                    print(f"Updating presentation status from pending to {data['status']}")
                    presentation.bank_reference = data['bank_reference']
                    presentation.status = data['status']

                    # If status is being set to 'discounted', update all receipts
                    if data['status'] == 'discounted':
                        for pr in presentation.presentation_receipts.all():
                            receipt = pr.checkreceipt or pr.lcn
                            if receipt:
                                receipt.status = 'DISCOUNTED'
                                receipt.save()

                    presentation.save()
                    print("Presentation updated successfully")

                elif (presentation.status == 'presented' or presentation.status == 'discounted'):
                    if 'receipt_statuses' in data:
                        receipt_statuses = data['receipt_statuses']
                        print(f"Processing {len(receipt_statuses)} receipt status updates: {receipt_statuses}")
                        
                        for receipt_id, new_status in receipt_statuses.items():
                            print(f"\nProcessing receipt {receipt_id}:")
                            print(f"New status data: {new_status}")
                            
                            if not new_status:
                                print("Skipping empty status update")
                                continue
                                
                            try:
                                presentation_receipt = PresentationReceipt.objects.get(
                                    id=receipt_id,
                                    presentation=presentation
                                )
                                print(f"Found presentation receipt: {presentation_receipt.__dict__}")
                                
                                receipt = presentation_receipt.checkreceipt or presentation_receipt.lcn
                                print(f"Associated receipt: {receipt.__dict__ if receipt else None}")
                                
                                if receipt and receipt.status not in ['PAID', 'UNPAID', 'COMPENSATED']:
                                    status_value = new_status['status'] if isinstance(new_status, dict) else new_status
                                    print(f"Processing status update to {status_value}")
                                    
                                    if status_value == 'unpaid':
                                        cause = new_status.get('cause') if isinstance(new_status, dict) else None
                                        unpaid_date = new_status.get('unpaid_date')
                                        print(f"Processing unpaid status with cause: {cause}")
                                        if not cause:
                                            raise ValidationError("Rejection cause required for unpaid status")
                                        # Add this line after successful unpaid update
                                        presentation_receipt.recorded_status = 'UNPAID'
                                        presentation_receipt.save()
                                        receipt.mark_as_unpaid(cause, unpaid_date)
                                    else:
                                        print(f"Updating status to: {status_value.upper()}")
                                        # Add this line after successful paid update
                                        presentation_receipt.recorded_status = status_value.upper()
                                        presentation_receipt.save()
                                        receipt.status = status_value.upper()
                                        receipt.save()
                                        
                                        if status_value.upper() == 'PAID':
                                            print("Receipt marked as paid, updating compensated receipts")
                                            receipt.update_compensated_receipts()
                                    
                                    print("Status update completed successfully")
                                else:
                                    print(f"Skipping receipt with status: {receipt.status if receipt else 'None'}")

                            except PresentationReceipt.DoesNotExist:
                                print(f"Error: Receipt {receipt_id} not found in presentation {pk}")
                                continue
                            except Exception as e:
                                print(f"Error processing receipt {receipt_id}: {str(e)}")
                                print(traceback.format_exc())
                                raise
                
                print("Presentation update completed successfully")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Presentation updated successfully'
                })

        except Exception as e:
            print("=== Error in presentation edit ===")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)    
   
@method_decorator(csrf_exempt, name='dispatch')
class PresentationDeleteView(View):
    """
    Handle deletion of presentations, resetting the status of associated receipts.
    """
    def post(self, request, pk):
            print(f"Delete request received for presentation {pk}")
            try:
                with transaction.atomic():
                    presentation = get_object_or_404(Presentation, pk=pk)
                    
                    # Only allow deletion of pending presentations
                    if presentation.status != 'pending':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Only pending presentations can be deleted'
                        }, status=400)
                    
                    # Get all related receipts before deletion
                    related_receipts = []
                    for pr in presentation.presentation_receipts.all():
                        receipt = pr.checkreceipt or pr.lcn
                        if receipt:
                            related_receipts.append(receipt)

                    # Delete presentation-related history entries for all receipts
                    content_types = ContentType.objects.get_for_model(CheckReceipt), ContentType.objects.get_for_model(LCN)
                    for receipt in related_receipts:
                        ReceiptHistory.objects.filter(
                            content_type__in=content_types,
                            object_id=receipt.id,
                            new_value__contains=str(presentation.id)  # Look for presentation ID in the new_value JSON
                        ).delete()
                        
                        # Reset receipt status back to PORTFOLIO
                        receipt.status = 'PORTFOLIO'
                        receipt.save()
                    
                    # Delete the presentation
                    presentation.delete()
                    print(f"Presentation {pk} deleted successfully")

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Presentation deleted successfully'
                    })

            except Presentation.DoesNotExist:
                print(f"Presentation {pk} not found")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Presentation not found'
                }, status=404)
            except Exception as e:
                print(f"Error deleting presentation {pk}: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to delete presentation: {str(e)}'
                }, status=500)

class AvailableReceiptsView(View):
    """
    Return a list of receipts available for presentation (in portfolio status).
    """
    def get(self, request):
        receipt_type = request.GET.get('type')
        presentation_type = request.GET.get('presentation_type')  # Add this line
        
        if receipt_type == 'check':
            receipts = CheckReceipt.objects.filter(
                status__in=[
                    CheckReceipt.STATUS_PORTFOLIO,
                    CheckReceipt.STATUS_UNPAID
                ]
            ).select_related('client', 'entity')
        else:  # lcn
            receipts = LCN.objects.filter(
                status__in=[
                    LCN.STATUS_PORTFOLIO,
                    LCN.STATUS_UNPAID
                ]
            ).select_related('client', 'entity')
            
            # Add LCN discount validation
            if presentation_type == 'DISCOUNT':
                valid_receipts = []
                for receipt in receipts:
                    days_to_due = (receipt.due_date - timezone.now().date()).days
                    if 20 <= days_to_due <= 120:
                        valid_receipts.append(receipt)
                receipts = valid_receipts
        
        # Get presentation info for unpaid receipts
        for receipt in receipts:
            if receipt.status == 'UNPAID':
                if receipt_type == 'check':
                    presentation = receipt.check_presentations.order_by('-presentation__date').first()
                else:
                    presentation = receipt.lcn_presentations.order_by('-presentation__date').first()
                
                if presentation:
                    receipt.last_presentation_date = presentation.presentation.date
            
            # Add days to due calculation for all receipts
            if hasattr(receipt, 'due_date'):
                receipt.days_to_due = (receipt.due_date - timezone.now().date()).days

        html = render_to_string('presentation/available_receipts.html', {
            'receipts': receipts
        }, request=request)
        
        return JsonResponse({'html': html})

class DiscountInfoView(View):
    def get(self, request, bank_account_id):
        try:
            bank_account = get_object_or_404(BankAccount, id=bank_account_id)
            receipt_type = request.GET.get('type', 'check')
            
            if receipt_type == 'check':
                available = bank_account.get_available_check_discount_line()
                total = bank_account.check_discount_line_amount or Decimal('0.00')
            else:
                available = bank_account.get_available_lcn_discount_line()
                total = bank_account.lcn_discount_line_amount or Decimal('0.00')
            
            used = total - available
            
            return JsonResponse({
                'total_amount': str(total),
                'used_amount': str(used),
                'available_amount': str(available)
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

class PresentationFilterView(View):
    def get(self, request):
        filters = Q()
        print("\n=== Presentation Filter Request ===")
        print(f"Parameters: {request.GET}")

        try:
            # Type filter
            pres_type = request.GET.get('presentation_type')
            if pres_type:
                filters &= Q(presentation_type=pres_type)

            # Bank account filter
            bank_account = request.GET.get('bank_account')
            if bank_account:
                filters &= Q(bank_account_id=bank_account)

            # Bank reference filter
            bank_ref = request.GET.get('bank_reference')
            if bank_ref:
                filters &= Q(bank_reference__icontains=bank_ref)

            # Date range filters
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            if date_from:
                filters &= Q(date__gte=date_from)
            if date_to:
                filters &= Q(date__lte=date_to)

            # Receipt number filter
            receipt_number = request.GET.get('receipt_number')
            if receipt_number:
                # Search in both check and LCN presentations
                receipt_presentations = PresentationReceipt.objects.filter(
                    Q(checkreceipt__check_number__icontains=receipt_number) |
                    Q(lcn__lcn_number__icontains=receipt_number)
                ).values_list('presentation_id', flat=True)
                filters &= Q(id__in=receipt_presentations)

            print(f"Applied filters: {filters}")

            # Get filtered presentations
            presentations = Presentation.objects.filter(filters).select_related(
                'bank_account'
            ).prefetch_related(
                'presentation_receipts__checkreceipt',
                'presentation_receipts__lcn'
            )

            print(f"Found {presentations.count()} presentations")

            # Render filtered results
            html = render_to_string('presentation/partials/presentations_table.html', {
                'presentations': presentations
            }, request=request)

            return JsonResponse({'html': html})

        except Exception as e:
            print(f"Error in presentation filter: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=400)
```

# views_receipts.py

```py
from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, request
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import calendar
from .models import CheckReceipt, LCN, CashReceipt, TransferReceipt, BankAccount, Client, Entity, ReceiptHistory, MOROCCAN_BANKS
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
import traceback


class ReceiptListView(ListView):
    template_name = 'receipt/receipt_list.html'
    context_object_name = 'receipts'

    def get_queryset(self):
        print("\n=== Getting Receipt Queryset ===")
        checks = CheckReceipt.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'check_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {checks.count()} checks")
        
        lcns = LCN.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'lcn_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {lcns.count()} LCNs")

        # Debug presentation info
        for check in checks:
            pres = check.check_presentations.first()
            if pres:
                print(f"Check {check.id} presentation: {pres.presentation.id}")
                print(f"Bank: {pres.presentation.bank_account}")

        return {
            'checks': checks,
            'lcns': lcns,
            'cash': CashReceipt.objects.select_related('client', 'entity', 'bank_account','credited_account').all(),
            'transfers': TransferReceipt.objects.select_related('client', 'entity', 'bank_account','credited_account').all()
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        print("\n=== Debug Context Data ===")
        # Add bank accounts for credited_account filter
        bank_accounts = BankAccount.objects.filter(is_active=True)
        context['bank_accounts'] = bank_accounts
        print(f"Added {bank_accounts.count()} bank accounts")

        # Add Moroccan banks for issuing_bank filter
        context['bank_choices'] = MOROCCAN_BANKS
        print(f"Added bank choices: {MOROCCAN_BANKS}")

        return context

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptCreateView(View):
    def get(self, request, receipt_type):
        print(f"Loading form for receipt type: {receipt_type}")
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
            'bank_accounts': bank_accounts,
            'bank_choices': MOROCCAN_BANKS, 
        }
        print(f"Context receipt_type: {context['receipt_type']}") 
        rendered = render(request, 'receipt/receipt_form_modal.html', context)
        print(f"Form HTML contains transfer fields: {'transfer_date' in rendered.content.decode()}")  # Debug
        return rendered
    
    def post(self, request, receipt_type):
        print("POST request received:")
        print("Receipt type:", receipt_type)
        print("Raw POST data:", request.body)
        data = request.POST.dict()
        print("POST data:", request.POST)
        print("transfer_date value:", request.POST.get('transfer_date'))
        print("transfer_reference value:", request.POST.get('transfer_reference'))
        
        try:
            data = request.POST.dict()

            compensates_id = data.pop('compensates', None)

            # Convert amount to Decimal
            data['amount'] = Decimal(data['amount'].replace(',', ''))
            
            # Common fields for all receipt types
            common_fields = {
                'client_id': data['client'],
                'entity_id': data['entity'],
                'operation_date': data['operation_date'],
                'amount': data['amount'],
                'client_year': data['client_year'],
                'client_month': data['client_month'],
                'notes': data.get('notes', '')
            }

            if receipt_type == 'check':
                receipt = CheckReceipt.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    check_number=data['check_number'],
                    branch=data.get('branch', '')
                )
            
            elif receipt_type == 'lcn':
                receipt = LCN.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    lcn_number=data['lcn_number'],
                )
            
            elif receipt_type == 'cash':
                receipt = CashReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    bank_account_id=data['credited_account'],
                    reference_number=data.get('reference_number', '')
                )
            
            elif receipt_type == 'transfer':
                receipt = TransferReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    bank_account_id=data['credited_account'],
                    transfer_reference=data.get('transfer_reference', ''),
                    transfer_date=data.get('transfer_date')
                )

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid receipt type'
                }, status=400)
            
            # Handle compensation if selected
            if compensates_id:
                # Find the unpaid receipt
                unpaid_receipt = None
                try:
                    unpaid_receipt = CheckReceipt.objects.get(
                        id=compensates_id, 
                        status=CheckReceipt.STATUS_UNPAID
                    )
                except CheckReceipt.DoesNotExist:
                    try:
                        unpaid_receipt = LCN.objects.get(
                            id=compensates_id, 
                            status=LCN.STATUS_UNPAID
                        )
                    except LCN.DoesNotExist:
                        pass
                
                if unpaid_receipt:
                    unpaid_receipt.compensate_with(receipt)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} created successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptUpdateView(View):
    def get(self, request, receipt_type, pk):
        print("\n=== Starting ReceiptUpdateView.get ===")
        print(f"Receipt type: {receipt_type}")
        print(f"Receipt ID: {pk}")
        
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        try:
            print(f"Looking for receipt with pk: {pk}")
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            print(f"Found receipt: {receipt}")
            print(f"Receipt attributes: {receipt.__dict__}")

            # Get current date info for form
            today = timezone.now()
            year_choices = range(today.year - 2, today.year + 1)
            month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
            bank_accounts = BankAccount.objects.filter(is_active=True)

            print("\nPreparing context:")
            context = {
                'receipt_type': receipt_type,
                'receipt': receipt,
                'title': f'Edit {receipt_type.title()} Receipt',
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
                },
                'bank_choices': MOROCCAN_BANKS,
            }
            print("Context prepared:", context)
            
            try:
                print("\nAttempting to render template...")
                rendered = render(request, 'receipt/receipt_form_modal.html', context)
                print("Template rendered successfully")
                return rendered
            except Exception as template_error:
                import traceback
                print("\nTemplate rendering error:")
                print(traceback.format_exc())
                raise template_error

        except Exception as e:
            import traceback
            print("\n=== Error in ReceiptUpdateView ===")
            print(traceback.format_exc())
            print("=======================================")
            return JsonResponse({
                'status': 'error',
                'message': f"Detail view error: {str(e)}",
                'traceback': traceback.format_exc()
            }, status=400)

    def post(self, request, receipt_type, pk):
        import traceback
        try:
            data = request.POST.dict()
            print(f"Received data for {receipt_type} update:", data)
            
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
            receipt.notes = data.get('notes', '')

            # Update type-specific fields
            if receipt_type in ['check', 'lcn']:
                receipt.issuing_bank = data['issuing_bank']  # Set issuing bank
                receipt.due_date = data['due_date']
                if receipt_type == 'check':
                    receipt.check_number = data['check_number']
                    receipt.branch = data.get('branch', '')
                else:
                    receipt.lcn_number = data['lcn_number']
            else:  # cash or transfer
                receipt.credited_account_id = data['credited_account']
                receipt.bank_account_id = data['credited_account'] 
                if receipt_type == 'transfer':  
                    receipt.transfer_reference = data['transfer_reference'] 
                    receipt.transfer_date = data['transfer_date']

            receipt.save()
            print(f"{receipt_type} updated successfully:", receipt)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} updated successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            print("Error in receipt update:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDeleteView(View):
    def post(self, request, receipt_type, pk):
        try:
            model_map = {
                'check': CheckReceipt,
                'lcn': LCN,
                'cash': CashReceipt,
                'transfer': TransferReceipt
            }
            
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Check if receipt can be deleted
            if receipt_type in ['check', 'lcn']:
                presentations = receipt.check_presentations.all() if receipt_type == 'check' else receipt.lcn_presentations.all()
                if presentations.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Cannot delete receipt that is part of a presentation'
                    }, status=400)

            receipt.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} deleted successfully'
            })
        except Exception as e:
            print("Error in receipt deletion:")
            print(traceback.format_exc())
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

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptStatusUpdateView(View):
    """Handle receipt status updates including unpaid marking"""
    def post(self, request, receipt_type, pk):
        try:
            data = json.loads(request.body)
            model = CheckReceipt if receipt_type == 'check' else LCN
            receipt = get_object_or_404(model, pk=pk)
            
            status = data.get('status')
            cause = data.get('cause')
            
            if status == 'unpaid':
                if not cause:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Rejection cause is required'
                    }, status=400)
                receipt.mark_as_unpaid(cause)
            else:
                receipt.status = status
                receipt.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Receipt status updated to {status}'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UnpaidReceiptsView(View):
    """API endpoint to list unpaid receipts for compensation selection"""
    def get(self, request):
        search = request.GET.get('search', '')
        
        # Query both check and LCN models for unpaid receipts
        unpaid_checks = CheckReceipt.objects.filter(
            status=CheckReceipt.STATUS_UNPAID,
            compensating_receipt__isnull=True
        ).select_related('entity')
        
        unpaid_lcns = LCN.objects.filter(
            status=LCN.STATUS_UNPAID,
            compensating_receipt__isnull=True
        ).select_related('entity')
        
        if search:
            unpaid_checks = unpaid_checks.filter(
                Q(check_number__icontains=search) |
                Q(entity__name__icontains=search)
            )
            unpaid_lcns = unpaid_lcns.filter(
                Q(lcn_number__icontains=search) |
                Q(entity__name__icontains=search)
            )
        
        # Format results
        results = []
        for check in unpaid_checks:
            results.append({
                'id': str(check.id),
                'type': 'Check',
                'number': check.check_number,
                'entity': check.entity.name,
                'amount': float(check.amount),
                'date': check.operation_date.strftime('%Y-%m-%d'),
                'url': reverse('receipt-detail', kwargs={'receipt_type': 'check', 'pk': check.id})
            })
            
        for lcn in unpaid_lcns:
            results.append({
                'id': str(lcn.id),
                'type': 'LCN',
                'number': lcn.lcn_number,
                'entity': lcn.entity.name,
                'amount': float(lcn.amount),
                'date': lcn.operation_date.strftime('%Y-%m-%d'),
                'url': reverse('receipt-detail', kwargs={'receipt_type': 'lcn', 'pk': lcn.id})
            })
            
        return JsonResponse({
            'items': results,
            'has_more': False  # Implement pagination if needed
        })
    
# In views_receipts.py - add the following class

class ReceiptTimelineView(View):
    def get(self, request, receipt_type, pk):
        try:
            # Get the receipt
            if receipt_type == 'check':
                receipt = get_object_or_404(CheckReceipt, pk=pk)
            else:
                receipt = get_object_or_404(LCN, pk=pk)

            # Get the receipt's history
            content_type = ContentType.objects.get_for_model(receipt)
            history = ReceiptHistory.objects.filter(
                content_type=content_type,
                object_id=receipt.id
            ).select_related('user')

            context = {
                'receipt': receipt,
                'history': history,
            }

            return render(request, 'receipt/receipt_timeline_modal.html', context)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

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

def unpaid_receipt_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    
    # Search across CheckReceipt and LCN
    unpaid_checks = CheckReceipt.objects.filter(
        status=CheckReceipt.STATUS_UNPAID
    ).filter(
        check_number__icontains=search
    )[:10]
    
    unpaid_lcns = LCN.objects.filter(
        status=LCN.STATUS_UNPAID
    ).filter(
        lcn_number__icontains=search
    )[:10]
    
    # Combine results
    results = []
    
    for check in unpaid_checks:
        results.append({
            'id': str(check.id),
            'text': f"Check #{check.check_number} ({check.entity.name}) - {check.amount} [{check.get_rejection_cause_display() or 'No cause'}]",
            'description': f"Check #{check.check_number} ({check.entity.name}) - {check.amount} [{check.get_rejection_cause_display() or 'No cause'}]"
        })
    
    for lcn in unpaid_lcns:
        results.append({
            'id': str(lcn.id),
            'text': f"LCN #{lcn.lcn_number} ({lcn.entity.name}) - {lcn.amount} [{lcn.get_rejection_cause_display() or 'No cause'}]",
            'description': f"LCN #{lcn.lcn_number} ({lcn.entity.name}) - {lcn.amount} [{lcn.get_rejection_cause_display() or 'No cause'}]"
        })
    
    print(f"Unpaid Receipt results({len(results)}): {results}")
    return JsonResponse({'results': results})

class ReceiptFilterView(View):
    def get(self, request):
        receipt_type = request.GET.get('type')
        filters = Q()

        # Get base queryset based on type
        model_map = {
                'checks': CheckReceipt,
                'lcns': LCN,
                'cash': CashReceipt,
                'transfers': TransferReceipt
            }
        
        # Log incoming request
        print(f"\n=== Filter Request ===")
        print(f"Receipt type: {receipt_type}")
        print(f"Parameters: {request.GET}")

        try:
            # Common filters
            client_id = request.GET.get('client')
            entity_id = request.GET.get('entity')
            if client_id:
                filters &= Q(client_id=client_id)
            if entity_id:
                filters &= Q(entity_id=entity_id)

            # Amount range filters
            amount_from = request.GET.get('amount_from')
            amount_to = request.GET.get('amount_to')
            if amount_from:
                filters &= Q(amount__gte=amount_from)
            if amount_to:
                filters &= Q(amount__lte=amount_to)

            # Creation date range filters
            creation_date_from = request.GET.get('creation_date_from')
            creation_date_to = request.GET.get('creation_date_to')
            if creation_date_from:
                filters &= Q(operation_date__gte=creation_date_from)
            if creation_date_to:
                filters &= Q(operation_date__lte=creation_date_to)

            # Due date range filters
            due_date_from = request.GET.get('due_date_from')
            due_date_to = request.GET.get('due_date_to')
            if due_date_from:
                filters &= Q(due_date__gte=due_date_from)
            if due_date_to:
                filters &= Q(due_date__lte=due_date_to)

            # Type-specific filters
            if receipt_type in ['checks', 'lcns']:
                status = request.GET.get('status')
                number = request.GET.get('number')
                if status:
                    filters &= Q(status=status)
                if number:
                    field_name = 'check_number' if receipt_type == 'checks' else 'lcn_number'
                    filters &= Q(**{f'{field_name}__icontains': number})
            
            elif receipt_type in ['cash', 'transfers']:
                credited_account = request.GET.get('credited_account')
                if credited_account:
                    filters &= Q(credited_account=credited_account)

            # Add issuing bank filter
            issuing_bank = request.GET.get('issuing_bank')
            if issuing_bank:
                filters &= Q(issuing_bank=issuing_bank)

            print(f"Applied filters: {filters}")

            queryset = model_map[receipt_type].objects.filter(filters)
            
            # Debug the query
            print(f"Query SQL: {queryset.query}")
            print(f"Found {queryset.count()} records")
            if issuing_bank:
                print(f"Filtered by bank {issuing_bank}: {list(queryset.values_list('issuing_bank', flat=True))}")

            # Historical status filter
            historical_status = request.GET.get('historical_status')
            if historical_status:
                content_type = ContentType.objects.get_for_model(model_map[receipt_type])
                # Sample of recent history records for this receipt type
                print("\n=== Recent History Records Sample ===")
                recent_records = ReceiptHistory.objects.filter(
                    content_type=content_type
                ).order_by('-timestamp')[:5]

                print("Last 5 history records structure:")
                for record in recent_records:
                    print(f"\nRecord ID: {record.id}")
                    print(f"Object ID: {record.object_id}")
                    print(f"Action: {record.action}")
                    print(f"New Value: {record.new_value}")


                print("\n=== Historical Status Debug ===")
                print(f"Looking for status: {historical_status}")
                print(f"Content type: {content_type}")
                
                # Check what's in ReceiptHistory
                history_records = ReceiptHistory.objects.filter(
                    content_type=content_type,
                    new_value__status=historical_status
                )
                
                print(f"Found {history_records.count()} history records:")
                for record in history_records:
                    print(f"- Receipt {record.object_id}: {record.new_value}")
                
                receipt_ids = history_records.values_list('object_id', flat=True)
                print(f"Receipt IDs found: {list(receipt_ids)}")
                
                filters &= Q(id__in=receipt_ids)


            print(f"Applied filters: {filters}")

            queryset = model_map[receipt_type].objects.filter(filters)
            
            print(f"Found {queryset.count()} records")

            html = render_to_string(f'receipt/partials/{receipt_type}_list.html', {
                'receipts': queryset
            }, request=request)

            return JsonResponse({'html': html})

        except Exception as e:
            print(f"Error in filter view: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=400)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = MOROCCAN_BANKS
        bank_accounts = BankAccount.objects.filter(is_active=True)
        print("Bank accounts being passed to context:", bank_accounts.count())  # Debug log
        context['bank_accounts'] = bank_accounts
        return context

```

# views_statement.py

```py
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import BankAccount, BankStatement, AccountingEntry, BankFeeType
import json
from decimal import Decimal
from django.db.models import Q
from datetime import datetime, date
import calendar

class BankStatementView(View):
    """View for displaying bank statements"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters or set defaults
            today = date.today()
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not start_date and not end_date:
                # Set to first and last day of current month
                start_date = date(today.year, today.month, 1)
                end_date = date(today.year, today.month, 
                              calendar.monthrange(today.year, today.month)[1])
            else:
                # Convert string dates to date objects if provided
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get statement entries
            entries = BankStatement.get_statement(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
             # Calculate totals excluding opening balance
            total_debit = sum(entry['debit'] or 0 for entry in entries if entry['type'] != 'BALANCE')
            total_credit = sum(entry['credit'] or 0 for entry in entries if entry['type'] != 'BALANCE')
            # Final balance comes from the first entry (they're sorted in reverse)
            final_balance = entries[0]['balance'] if entries else Decimal('0.00')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'bank/partials/statement_table.html',
                        {'entries': entries},
                        request=request
                    ),
                    'totals': {
                        'debit': total_debit,
                        'credit': total_credit,
                        'balance': final_balance
                    }
                })
            
            # Get additional data for full page render
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'bank_accounts': BankAccount.objects.filter(is_active=True).exclude(id=bank_account.id),
                'fee_types': BankFeeType.objects.all(),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'final_balance': final_balance
            }
            
            return render(request, 'bank/bank_statement.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class AccountingView(View):
    """View for displaying accounting entries"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get accounting entries
            entries = AccountingEntry.get_entries(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'total_debit': sum(entry['debit'] or 0 for entry in entries),
                'total_credit': sum(entry['credit'] or 0 for entry in entries)
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string(
                    'bank/partials/accounting_table.html',
                    context,
                    request=request
                )
                return JsonResponse({'html': html})
            
            return render(request, 'bank/accounting.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class OtherOperationsView(View):
    """View for displaying other operations (discounted receipts)"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get accounting entries filtered for journal code '06'
            entries = AccountingEntry.get_entries(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter for other operations (journal code '06')
            entries = [e for e in entries if e['journal_code'] == '06']
            
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'total_debit': sum(entry['debit'] or 0 for entry in entries),
                'total_credit': sum(entry['credit'] or 0 for entry in entries)
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string(
                    'bank/partials/other_operations_table.html',
                    context,
                    request=request
                )
                return JsonResponse({'html': html})
            
            return render(request, 'bank/other_operations.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
```

# views_transfer.py

```py
# views_transfer.py

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import InterBankTransfer, TransferredRecord, BankAccount, BankStatement
import json
from decimal import Decimal
from django.db import transaction
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils import timezone

class CreateTransferView(View):
    """Handle creation of interbank transfers"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Validate basic data
                from_bank = get_object_or_404(BankAccount, id=data['from_bank'])
                to_bank = get_object_or_404(BankAccount, id=data['to_bank'])
                
                if from_bank == to_bank:
                    raise ValidationError("Cannot transfer to the same bank account")
                    
                # Create the transfer
                total_amount = Decimal('0.00')
                records_to_transfer = data['records']
                
                # Validate records are available for transfer
                for record in records_to_transfer:
                    if TransferredRecord.objects.filter(
                        source_type=record['source_type'],
                        source_id=record['source_id']
                    ).exists():
                        raise ValidationError(f"Record {record['source_id']} has already been transferred")
                    
                    total_amount += Decimal(str(record['amount']))

                # Check available balance
                current_balance = BankStatement.calculate_balance_until(from_bank, timezone.now().date())
                if current_balance < total_amount:
                    raise ValidationError(f"Insufficient balance. Available: {current_balance}, Required: {total_amount}")
                
                # Create transfer
                transfer = InterBankTransfer.objects.create(
                    from_bank=from_bank,
                    to_bank=to_bank,
                    date=data['date'],
                    label=data.get('label', 'Interbank Transfer'),
                    total_amount=total_amount
                )
                
                # Create transferred records
                for record in records_to_transfer:
                    TransferredRecord.objects.create(
                        transfer=transfer,
                        source_type=record['source_type'],
                        source_id=record['source_id'],
                        amount=Decimal(str(record['amount'])),
                        original_date=record['date'],
                        original_label=record['label'],
                        original_reference=record['reference']
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Transfer created successfully',
                    'transfer_id': str(transfer.id)
                })
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to create transfer: {str(e)}'
            }, status=500)

class DeleteTransferView(View):
    """Handle deletion of interbank transfers"""
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                transfer = get_object_or_404(InterBankTransfer, pk=pk)
                
                # Get all transferred records before deletion
                transferred_records = transfer.transferred_records.all()
                
                # Delete the transferred records to remove the "transferred" status
                transferred_records.delete()
                
                # Soft delete the transfer
                transfer.is_deleted = True
                transfer.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Transfer deleted successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to delete transfer: {str(e)}'
            }, status=500)
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

