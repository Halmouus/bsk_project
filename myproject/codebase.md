# testapp/models.py

```py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from .base import BaseModel
from datetime import timedelta 
import random
import string
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q




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
    
class Checker(BaseModel):
    TYPE_CHOICES = [
        ('CHQ', 'Cheque'),
        ('LCN', 'LCN')
    ]
    
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
    
    PAGE_CHOICES = [
        (25, '25'),
        (50, '50'),
        (100, '100')
    ]

    code = models.CharField(max_length=10, unique=True, blank=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    bank = models.CharField(max_length=4, choices=BANK_CHOICES)
    account_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d+$', 'Only numeric characters allowed.')]
    )
    city = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[A-Za-z\s]+$', 'Only alphabetical characters allowed.')]
    )
    owner = models.CharField(max_length=100, default="Briqueterie Sidi Kacem")
    num_pages = models.IntegerField(choices=PAGE_CHOICES)
    index = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')]
    )
    starting_page = models.IntegerField(validators=[MinValueValidator(1)])
    final_page = models.IntegerField(blank=True)
    current_position = models.IntegerField(blank=True)

    @property
    def remaining_pages(self):
        print(f"Calculating remaining pages for {self.bank}")
        print(f"final_page: {self.final_page}")
        print(f"current_position: {self.current_position}")
        return self.final_page - self.current_position + 1

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.final_page:
            self.final_page = self.starting_page + self.num_pages - 1
        if not self.current_position:
            self.current_position = self.starting_page
        print(f"Saving checker for {self.bank}")
        print(f"current_position: {self.current_position}")
        super().save(*args, **kwargs)

    def generate_code(self):
        # Generate random alphanumeric code
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def __str__(self):
        return f'Checker {self.index}'

    class Meta:
        ordering = ['-created_at']

class Check(BaseModel):
    checker = models.ForeignKey(Checker, on_delete=models.PROTECT, related_name='checks')
    position = models.CharField(max_length=10)  # Will store "INDEX + position number"
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
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    
    def save(self, *args, **kwargs):
        print(f"New creation at:  {self.checker.current_position}")
        if not self.position:
            self.position = f"{self.checker.index}{self.checker.current_position}"
        if not self.amount_due:
            self.amount_due = self.cause.total_amount
        super().save(*args, **kwargs)
        
        # Update checker's current position
        if self.checker.current_position == int(self.position[len(self.checker.index):]):
            self.checker.current_position += 1
            self.checker.save()

    def clean(self):
        if self.paid_at and not self.delivered_at:
            raise ValidationError("Check cannot be marked as paid before delivery")

    class Meta:
        ordering = ['-creation_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__lte=models.F('amount_due')),
                name='check_amount_cannot_exceed_due'
            )
        ]
```

# testapp/signals.py

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

```

# testapp/templates/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MyProject{% endblock %}</title>
    
    <!-- Bootstrap 4.5 CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">

    <!-- jQuery and Bootstrap 4.5 JS -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    <link rel="stylesheet" href="{% static 'css/styles.css' %}">
</head>
<body>
    <!-- Header / Navigation Bar -->
<header>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <a class="navbar-brand" href="{% url 'login' %}">MyProject</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ml-auto">
                {% if user.is_authenticated %}
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle hover-trigger" href="#" id="supplierDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Supplier
                        </a>
                        <div class="dropdown-menu dropdown-hover" aria-labelledby="supplierDropdown">
                            <a class="dropdown-item hover-highlight" href="{% url 'supplier-list' %}">Suppliers</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'product-list' %}">Products</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'invoice-list' %}">Invoices</a>
                        </div>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle hover-trigger" href="#" id="checkDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Check/Checkers
                        </a>
                        <div class="dropdown-menu dropdown-hover" aria-labelledby="checkDropdown">
                            <a class="dropdown-item hover-highlight" href="{% url 'checker-list' %}">Checkers</a>
                            <a class="dropdown-item hover-highlight" href="{% url 'check-list' %}">Checks</a>
                        </div>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'profile' %}">Profile</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'logout' %}">Logout</a>
                    </li>
                {% else %}
                    <li class="nav-item">
                        <a class="nav-link hover-trigger" href="{% url 'login' %}">Login</a>
                    </li>
                {% endif %}
            </ul>
        </div>
    </nav>
</header>

    <!-- Message Alerts -->
    <div id="alerts-container" class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" role="alert">
                    {% if message.tags == 'error' %}
                        <i class="fas fa-exclamation-triangle"></i>
                    {% endif %}
                    <strong>{{ message|safe }}</strong>
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Main Content Block -->
    <main class="container-fluid mt-4">
        {% block content %}
        <!-- Page-specific content goes here -->
        {% endblock %}
    </main>

    <!-- Footer -->
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">&copy; 2024 MyProject. All rights reserved.</span>
            <div>
                <a href="#" class="text-muted mx-2">Privacy</a>
                <a href="#" class="text-muted mx-2">Terms</a>
                <a href="#" class="text-muted mx-2">Support</a>
            </div>
        </div>
    </footer>

    <!-- Custom JavaScript -->
    <script src="{% static 'js/scripts.js' %}"></script>

    <script>
        // Fading Alerts
        $(document).ready(function() {
            setTimeout(function() {
                $(".alert").fadeOut("slow");
            }, 5000);

            // Dropdown on Hover
            $(".hover-trigger").hover(function() {
                $(this).parent().addClass('show');
                $(this).siblings('.dropdown-menu').addClass('show').stop(true, true).slideDown(200);
            }, function() {
                $(this).parent().removeClass('show');
                $(this).siblings('.dropdown-menu').removeClass('show').stop(true, true).slideUp(200);
            });

            $(".dropdown-menu").hover(function() {
                $(this).addClass('show').stop(true, true).slideDown(200);
            }, function() {
                $(this).removeClass('show').stop(true, true).slideUp(200);
            });
        });
    </script>

    <style>
        /* Alert Styling */
        .alert {
            border-left: 5px solid;
        }
        .alert-danger {
            border-left-color: #dc3545;
        }
        .alert i {
            margin-right: 10px;
        }

        /* Navbar Hover Effects */
        .hover-trigger:hover {
            background-color: rgba(159, 165, 174, 0.2);
            transition: background-color 0.3s ease;
            text-decoration:underline;
        }

        /* Dropdown Menu Styling */
        .dropdown-menu {
            display: none;
        }
        .hover-highlight:hover {
            background-color: rgba(200, 52, 203, 0.1);
            transition: background-color 0.3s ease;
        }

        /* Footer Styling */
        .footer a {
            margin: 0 5px;
            color: inherit;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</body>
</html>

```

# testapp/templates/checker/check_list.html

```html
{% extends 'base.html' %}

{% load check_tags %}

{% block content %}
<div class="container-fluid mt-4">
    <h2>Checks List</h2>
    <div class="container-fluid px-1">  <!-- Add padding -->
        <div class="table-responsive">  <!-- Make table responsive -->
            <table class="table table-hover">
                <thead class="thead-dark">
                    <tr>
                        <th>Checker Code</th>
                        <th>Bank</th>
                        <th>Owner</th>
                        <th>Type</th>
                        <th>Position</th>
                        <th>Creation Date</th>
                        <th>Beneficiary</th>
                        <th>Invoice Ref</th>
                        <th>Payment Due</th>
                        <th>Amount Due</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for check in checks %}
                    <tr class="{% if check.status == 'paid' %}table-success{% elif check.status == 'cancelled' %}table-danger{% elif check.status == 'delivered' %}table-warning{% endif %}"
                        {% if check.cancelled_at %}data-cancelled="true" data-cancel-reason="{{ check.cancellation_reason }}"{% endif %}
                        {% if check.status == 'paid' %}data-paid="true"{% endif %}>

                        <td>{{ check.checker.code }}</td>
                        <td>{{ check.checker.get_bank_display }}</td>
                        <td>{{ check.checker.owner }}</td>
                        <td>{{ check.checker.get_type_display }}</td>
                        <td>{{ check.position }}</td>
                        <td>{{ check.creation_date|date:"Y-m-d" }}</td>
                        <td>{{ check.beneficiary.name }}</td>
                        <td>{{ check.cause.ref }}</td>
                        <td>{{ check.payment_due|date:"Y-m-d"|default:"-" }}</td>
                        <td class="text-right">{{ check.amount_due|floatformat:2 }}</td>
                        <td class="text-right">{{ check.amount|floatformat:2 }}</td>
                        <td>
                            {% if check.status == 'cancelled' %}
                            <span class="badge badge-danger cancellation-info" 
                                    role="button" 
                                    data-toggle="modal" 
                                    data-target="#cancellationDetailModal"
                                    data-reason="{{ check.cancellation_reason }}">
                                Cancelled
                            </span>
                            {% elif check.paid %}
                                <span class="badge badge-success">Paid</span>
                            {% elif check.delivered %}
                                <span class="badge badge-warning">Delivered</span>
                            {% else %}
                                <span class="badge badge-secondary">Pending</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">

                                <button class="btn btn-sm edit-check-btn
                                    {% if check.status == 'paid' or check.status == 'cancelled' %}btn-secondary{% else %}btn-primary{% endif %}"
                                    data-check-id="{{ check.id }}"
                                    {% if check.status == 'paid' or check.status == 'cancelled' %}disabled{% endif %}>
                                    {% if check.status == 'paid' or check.status == 'cancelled' %}
                                        <i class="fas fa-lock"></i> Edit
                                    {% else %}
                                    <i class="fas fa-edit"></i> Edit
                                    {% endif %}
                                </button>
                            
                                {% if not check.delivered and not check.status == 'paid' and not check.status == 'cancelled' %}
                                    <button class="btn btn-warning btn-sm mark-delivered" 
                                            data-check="{{ check.id }}">
                                        Mark Delivered
                                    </button>
                                {% endif %}
                                {% if check.delivered and not check.paid and not check.status == 'cancelled' %}
                                    <button class="btn btn-success btn-sm mark-paid" 
                                            data-check="{{ check.id }}">
                                        Mark Paid
                                    </button>
                                {% endif %}
                                {% if not check.paid and not check.status == 'cancelled' %}
                                    <button class="btn btn-danger btn-sm cancel-check-btn" 
                                            data-check-id="{{ check.id }}">
                                        Cancel
                                    </button>
                                {% endif %}
                                <button class="btn btn-info btn-sm">Print</button>
                            </div>
                        </td>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<div class="modal fade" id="editCheckModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Check</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <form id="edit-check-form">
                    <div class="form-group">
                        <label>Status: <span class="badge" id="check-status-badge"></span></label>
                    </div>
                    <div class="form-group">
                        <label for="delivered_at">Delivered At:</label>
                        <input type="datetime-local" id="delivered_at" class="form-control">
                    </div>
                    <div class="form-group">
                        <label for="paid_at">Paid At:</label>
                        <input type="datetime-local" id="paid_at" class="form-control">
                    </div>
                    
                    <!-- Cancel Check Button (only shown if not paid) -->
                    <div class="form-group" id="cancel-check-section">
                        <button type="button" class="btn btn-danger" id="cancel-check-btn">
                            Cancel Check
                        </button>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" id="save-check-btn">Save Changes</button>
            </div>
        </div>
    </div>
</div>

<!-- Cancellation Modal -->
<div class="modal fade" id="cancelCheckModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancel Check</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="cancellation_reason">Reason for Cancellation:</label>
                    <textarea id="cancellation_reason" class="form-control" placeholder="Reason for cancellation" rows="2" required ></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirm-cancel-btn">Confirm Cancellation</button>
            </div>
        </div>
    </div>
</div>

<!-- Cancellation Detail Modal -->
<div class="modal fade" id="cancellationDetailModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancellation Reason</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <p id="cancellationReason"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- Payment Details Modal -->
<div class="modal fade" id="paymentDetailsModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Payment Details</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="payment-info"></div>
            </div>
        </div>
    </div>
</div>

<style>
    .cancellation-info {
        cursor: pointer;
    }
    .cancellation-info:hover {
        opacity: 0.8;
    }
    
    /* Make buttons more refined */
    .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        border-radius: 0.25rem;
        transition: all 0.2s;
    }
    
    .btn i {
        font-size: 0.875rem;
    }
    
    .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Space out buttons in button groups */
    .btn-group .btn {
        margin-right: 0.25rem;
    }
    .btn-group .btn:last-child {
        margin-right: 0;
    }

    .table-responsive {
    margin-left: auto;
    margin-right: auto;
    padding: 0 15px; /* Minor borders on the left and right */
    max-width: 100%; /* Ensure it takes the entire width */
    }


    .table-hover tbody tr {
    height: 3rem; /* Increase row height */
    }

    .btn-secondary {
    background-color: #d6d6d6;
    color: #555;
    cursor: not-allowed;
    }

    .btn-secondary i {
        margin-right: 5px; /* Adds spacing between icon and text */
    }

</style>

<script>
$(document).ready(function() {
    let currentCheckId;

    // Disable controls for cancelled checks
    $('tr[data-cancelled="true"]').each(function() {
        const reason = $(this).data('cancel-reason');
        $(this).find('button').prop('disabled', true)
            .attr('title', `Check cancelled: ${reason}`);
    });

    $('.mark-delivered').click(function() {
        const checkId = $(this).data('check');
        if (confirm('Mark this check as delivered?')) {
            $.ajax({
                url: `/testapp/checks/${checkId}/mark-delivered/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error marking check as delivered');
                }
            });
        }
    });

    $('.mark-paid').click(function() {
        const checkId = $(this).data('check');
        if (confirm('Mark this check as paid?')) {
            $.ajax({
                url: `/testapp/checks/${checkId}/mark-paid/`,
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error marking check as paid');
                }
            });
        }
    });

     // Edit Check Modal
    $('.edit-check-btn').click(function() {
        const $row = $(this).closest('tr');
        if ($row.data('cancelled')) {
            alert(`Check cancelled: ${$row.data('cancel-reason')}`);
            return;
        }

        currentCheckId = $(this).data('check-id');
        console.log("Opening edit modal for check:", currentCheckId);
        
        $.ajax({
            url: `/testapp/checks/${currentCheckId}/`,
            method: 'GET',
            success: function(data) {
                console.log("Received data:", data); // Debug
                $('#delivered_at').val(data.delivered_at)
                    .prop('readonly', data.delivered_at != null);
                $('#paid_at').val(data.paid_at)
                    .prop('readonly', data.paid_at != null);
                
                // Update status badge
                const badgeClass = {
                    'pending': 'badge-warning',
                    'delivered': 'badge-info',
                    'paid': 'badge-success',
                    'cancelled': 'badge-danger'
                }[data.status];
            
                
                $('#check-status-badge')
                    .text(data.status.toUpperCase())
                    .removeClass()
                    .addClass(`badge ${badgeClass}`);
                
                // Show/hide cancel section based on status
                $('#cancel-section').toggle(!data.paid_at);
                $('#save-check-btn').prop('disabled', data.cancelled_at);
                
                $('#editCheckModal').modal('show');
            },
            error: function(xhr) {
                alert("Error loading check details");
            }
        });
    });
    
    // Save Check Changes
    $('#save-check-btn').click(function() {
        console.log("Saving changes for check:", currentCheckId);   

        $.ajax({
            url: `/testapp/checks/${currentCheckId}/`,
            method: 'POST',
            data: JSON.stringify({
                delivered_at: $('#delivered_at').val(),
                paid_at: $('#paid_at').val()
            }),
            contentType: 'application/json',
            success: function() {
                $('#editCheckModal').modal('hide');
                location.reload();
            },
            error: function(xhr) {
                alert(xhr.responseJSON.error|| "Error saving changes");
            }
        });
    });
    
    // Cancel Check
    $('#cancel-check-btn').click(function() {
        $('#editCheckModal').modal('hide');
        $('#cancelCheckModal').modal('show');
    });
    
    // Confirm Cancellation
    $('#confirm-cancel-btn').click(function() {
        const reason = $('#cancellation_reason').val();
        
        if (!reason.trim()) {
            alert('Please provide a reason for cancellation');
            return;
        }

        console.log("Cancelling check:", currentCheckId);
        $.ajax({
            url: `/testapp/checks/${currentCheckId}/cancel/`,
            method: 'POST',
            data: JSON.stringify({ reason: reason }),
            contentType: 'application/json',
            success: function() {
                $('#cancelCheckModal').modal('hide');
                location.reload();
            },
            error: function(xhr) {
                alert(xhr.responseJSON.error || "Error cancelling check");
            }
        });
    });

    // Display cancellation reason
    $('.cancellation-info').click(function() {
        const reason = $(this).data('reason');
        $('#cancellationReason').text(reason);
    });

    // Reset modals on close
    $('#editCheckModal, #cancelCheckModal').on('hidden.bs.modal', function() {
        $('#cancellation_reason').val('');
    });

    // Payment details popup
    $('.payment-info').click(function() {
        const checkId = $(this).data('check');
        $.ajax({
            url: `/testapp/checks/${checkId}/payment-details/`,
            success: function(data) {
                $('.payment-info').html(`
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-subtitle mb-3">Payment Information</h6>
                            <p><strong>Paid Amount:</strong> ${formatMoney(data.amount)}</p>
                            <p><strong>Payment Date:</strong> ${data.paid_at}</p>
                            <p><strong>Payment Reference:</strong> ${data.reference}</p>
                            <hr>
                            <h6 class="card-subtitle mb-3">Invoice Information</h6>
                            <p><strong>Invoice Ref:</strong> ${data.invoice_ref}</p>
                            <p><strong>Beneficiary:</strong> ${data.beneficiary}</p>
                            <p><strong>Original Amount:</strong> ${formatMoney(data.invoice_amount)}</p>
                        </div>
                    </div>
                `);
            }
        });
    });
    
});
</script>
{% endblock %}
```

# testapp/templates/checker/checker_list.html

```html
{% extends 'base.html' %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Checkers</h2>
        <button class="btn btn-primary" data-toggle="modal" data-target="#checkerModal">
            <i class="fas fa-plus"></i> Add New Checker
        </button>
    </div>

    <table class="table table-hover">
        <thead class="thead-dark">
            <tr>
                <th>Code</th>
                <th>Owner</th>
                <th>Type</th>
                <th>Bank</th>
                <th>Account</th>
                <th>City</th>
                <th>Starting Page</th>
                <th>Final Page</th>
                <th>Current Position</th>
                <th>Remaining Pages</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for checker in checkers %}
            <tr>
                <td>{{ checker.code }}</td>
                <td>{{ checker.owner }}</td>
                <td>{{ checker.get_type_display }}</td>
                <td>{{ checker.get_bank_display }}</td>
                <td>{{ checker.account_number }}</td>
                <td>{{ checker.city }}</td>
                <td>{{ checker.index }}{{ checker.starting_page }}</td>
                <td>{{ checker.index }}{{ checker.final_page }}</td>
                <td>{{ checker.index }}{{ checker.current_position }}</td>
                <td>{{ checker.remaining_pages }}</td>
                <td>
                    <button class="btn btn-primary btn-sm add-payment" data-checker="{{ checker.id }}">
                        <i class="fas fa-plus"></i> Add Payment
                    </button>
                    <button class="btn btn-info btn-sm view-details" data-checker="{{ checker.id }}">
                        Details
                    </button>
                    <button class="btn btn-danger btn-sm delete-checker" data-checker="{{ checker.id }}">
                        <i class="fas fa-times"></i> Delete
                    </button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Checker Modal -->
<div class="modal fade" id="checkerModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add New Checker</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form id="checker-form">
                    <div class="form-group">
                        <label>Type</label>
                        <select class="form-control" name="type" required>
                            <option value="CHQ">Cheque</option>
                            <option value="LCN">LCN</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Bank</label>
                        <select class="form-control" name="bank" required>
                            {% for code, name in bank_choices %}
                            <option value="{{ code }}">{{ name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Account Number</label>
                        <input type="text" id="account_number" name="account_number" 
                            class="form-control" 
                            pattern="\d+" 
                            oninput="this.value = this.value.replace(/[^0-9]/g, '')"
                            title="Only numbers allowed"
                            required>
                    </div>
                    <div class="form-group">
                        <label>City</label>
                        <input type="text" class="form-control" name="city" 
                               pattern="^[A-Za-z\s]+$" required>
                    </div>
                    <div class="form-group">
                        <label>Number of Pages</label>
                        <select class="form-control" name="num_pages" required>
                            <option value="25">25</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Index (3 uppercase letters)</label>
                        <input type="text" class="form-control" name="index" 
                               pattern="^[A-Z]{3}$" required>
                    </div>
                    <div class="form-group">
                        <label>Starting Page</label>
                        <input type="number" class="form-control" name="starting_page" 
                               min="1" required>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary" id="save-checker">Save</button>
            </div>
        </div>
    </div>
</div>

<!-- Payment Modal -->
<div class="modal fade" id="paymentModal" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Payment</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <!-- Payment Summary Cards -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Invoice Total</h6>
                                <h4 id="invoice-total" class="card-title mb-0">-</h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Already Issued</h6>
                                <h4 id="already-issued" class="card-title mb-0">-</h4>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Paid</h6>
                                <h4 id="amount-paid" class="card-title mb-0">-</h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Available</h6>
                                <h4 id="amount-available" class="card-title mb-0">-</h4>
                            </div>
                        </div>
                    </div>
                </div>
                <form id="payment-form">
                    <input type="hidden" id="checker_id" name="checker_id">
                    <div class="form-group">
                        <label>Position</label>
                        <input type="text" class="form-control" id="position" disabled>
                    </div>
                    <div class="form-group">
                        <label>Creation Date</label>
                        <input type="date" class="form-control" name="creation_date" 
                               value="{% now 'Y-m-d' %}">
                    </div>
                    <div class="form-group">
                        <label>Beneficiary</label>
                        <input type="text" class="form-control" id="beneficiary" 
                               placeholder="Search supplier...">
                        <input type="hidden" id="supplier_id">
                    </div>
                    <div class="form-group">
                        <label>Invoice</label>
                        <input type="text" class="form-control" id="invoice" 
                               placeholder="Search invoice..." disabled>
                        <input type="hidden" id="invoice_id" name="invoice_id">
                    </div>
                    <div class="form-group">
                        <label>Amount</label>
                        <input type="number" class="form-control" name="amount" step="0.01" required>
                        <div class="invalid-feedback">
                            Amount cannot exceed the available amount for payment.
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Payment Due Date</label>
                        <input type="date" class="form-control" name="payment_due">
                    </div>
                    <div class="form-group">
                        <label>Observation</label>
                        <textarea class="form-control" name="observation"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-success" id="save-and-clone">Save and Clone</button>
                <button type="button" class="btn btn-primary" id="save-payment">Save</button>
            </div>
        </div>
    </div>
</div>

<style>
    .ui-autocomplete {
        position: absolute;
        z-index: 2000; /* Make sure it appears above the modal */
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 0;
        max-height: 200px;
        overflow-y: auto;
        list-style: none;
    }

    .ui-menu-item {
        padding: 8px 12px;
        cursor: pointer;
    }

    .ui-menu-item:hover {
        background-color: #f8f9fa;
    }

    .ui-helper-hidden-accessible {
        display: none;
    }
</style>

<script>
$(document).ready(function() {
    console.log("Document ready");

    $('#save-checker').click(function() {
        console.log("Save button clicked"); 
        const form = $('#checker-form');
        const formData = {};
        
        form.serializeArray().forEach(item => {
            formData[item.name] = item.value;
        });

        console.log("Sending data:", formData); // Debug log

        $.ajax({
            url: "{% url 'checker-create' %}",
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            success: function(response) {
                console.log("Success:", response); // Debug log
                location.reload();
            },
            error: function(xhr, status, error) {
                console.error("Error:", xhr.responseText); // Debug log
                alert('Error creating checker: ' + xhr.responseText);
            }
        });
    });

    $('.add-payment').click(function() {
        const checkerId = $(this).data('checker');
        $('#checker_id').val(checkerId);
        
        // Load checker details to get current position
        $.ajax({
            url: `/testapp/checkers/${checkerId}/details/`,
            method: 'GET',
            success: function(data) {
                $('#position').val(`${data.index}${data.current_position}`);
                $('#paymentModal').modal('show');
            }
        });
    });

    // Beneficiary autocomplete
    $('#beneficiary').autocomplete({
        minLength: 2,
        source: function(request, response) {
            $.ajax({
                url: "{% url 'supplier-autocomplete' %}",
                data: { term: request.term },
                success: function(data) {
                    response($.map(data, function(item) {
                        return {
                            label: item.label,
                            value: item.value
                        };
                    }));
                }
            });
        },
        appendTo: "#paymentModal", // Make sure dropdown appears inside modal
        select: function(event, ui) {
            $('#beneficiary').val(ui.item.label.split(' (')[0]);
            $('#supplier_id').val(ui.item.value);
            $('#invoice').prop('disabled', false);
            return false;
        }
    }).data("ui-autocomplete")._renderItem = function(ul, item) {
        return $("<li>")
            .append("<div>" + item.label + "</div>")
            .appendTo(ul);
    };

    // Store the last valid amount
    let lastValidAmount = 0;

    // Enhanced amount validation
    $('input[name="amount"]').on('input blur', function(e) {
        const $input = $(this);
        const amount = parseFloat($input.val()) || 0;
        const availableText = $('#amount-available').text();
        const available = parseFloat(
            availableText
                .replace(/[^0-9.,-]+/g, '') // Remove non-numeric characters except '.' and ','
                .replace(/\s|(?<=\d)\./g, '') // Remove spaces or thousands separators (e.g., '.')
                .replace(',', '.') // Replace ',' with '.' for decimal compatibility
        ) || 0;

        console.log('Current amount:', amount); // Debug
        console.log('Available amount:', available); // Debug
        console.log('Is exceeding?', amount > available); // Debug
            
        if (e.type === 'input') {
            // Real-time validation feedback
            if (amount <= 0) {
                $input.addClass('is-invalid');
                $('.invalid-feedback').text('Amount must be greater than 0');
                $('#save-payment').prop('disabled', true);
            } else if (amount > available) {
                $input.addClass('is-invalid');
                $('.invalid-feedback').text(`Amount cannot exceed ${formatMoney(available)}`);
                console.log('Amount cannot exceed ', available); // Debug
                $('#save-payment').prop('disabled', true);
            } else {
                $input.removeClass('is-invalid');
                $('#save-payment').prop('disabled', false);
                lastValidAmount = amount; // Store the valid amount
            }
        } else if (e.type === 'blur') {
            // When leaving the field, revert to last valid amount if invalid
            if (amount <= 0 || amount > available) {
                console.log('Reverting to last valid amount:', lastValidAmount); // Debug
                $input.val(lastValidAmount.toFixed(2));
                $input.removeClass('is-invalid');
                $('#save-payment').prop('disabled', false);
            }
        }
    });

    // Invoice autocomplete
    $('#invoice').autocomplete({
        minLength: 2,
        source: function(request, response) {
            const supplierId = $('#supplier_id').val();
            console.log("Supplier ID for invoice search:", supplierId);  // Debug
            console.log("Search term:", request.term);  // Debug
            
            if (!supplierId) {
                console.log("No supplier selected");  // Debug
                return;
            }
            
            $.ajax({
                url: "{% url 'invoice-autocomplete' %}",
                data: { 
                    term: request.term,
                    supplier: supplierId
                },
                success: function(data) {
                    console.log("Received invoices:", data);  // Debug
                    response($.map(data, function(item) {
                        console.log("Mapping item:", item);  // Debug
                        return {
                            label: `${item.ref} (${item.date}) - ${item.status} - ${item.amount.toLocaleString()} MAD`,
                            value: item.id,
                            payment_info: item.payment_info,
                            ref: item.ref 
                        };
                    }));
                },
                error: function(xhr, status, error) {
                    console.error("Invoice search error:", error);  // Debug
                    console.error("Response:", xhr.responseText);  // Debug
                }
            });
        },
        select: function(event, ui) {
            const info = ui.item.payment_info;
            $('#invoice').val(ui.item.ref);
            $('#invoice_id').val(ui.item.value);

            // Update summary cards
            $('#invoice-total').text(formatMoney(info.total_amount));
            $('#already-issued').text(formatMoney(info.issued_amount));
            $('#amount-paid').text(formatMoney(info.paid_amount));
            $('#amount-available').text(formatMoney(info.available_amount));

            // Auto-fill amount field with available amount
            const initialAmount = info.available_amount;
            console.log('Setting initial amount:', initialAmount);
            lastValidAmount = initialAmount;
            $('input[name="amount"]').val(initialAmount.toFixed(2))
                                .removeClass('is-invalid');
            $('#save-payment').prop('disabled', false);

            return false;
        }
    });


    function formatMoney(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'MAD',
            minimumFractionDigits: 2
        }).format(amount);
    }

    $('#save-payment').click(function(e) {
        e.preventDefault();
        
        // Get form values
        const checkerId = $('#checker_id').val();
        const invoiceId = $('#invoice_id').val();
        const amount = parseFloat($('input[name="amount"]').val()) || 0;
        const paymentDue = $('input[name="payment_due"]').val();
        const observation = $('textarea[name="observation"]').val();

        // Validate required fields
        if (!checkerId || !invoiceId) {
            alert('Checker and Invoice are required');
            return;
        }

        // Prepare data for submission
        const data = {
            checker_id: checkerId,
            invoice_id: invoiceId,
            amount: amount,
            payment_due: paymentDue || null,
            observation: observation || ''
        };

        console.log('Sending data:', data); // Debug log

        // Send AJAX request
        $.ajax({
            url: "{% url 'check-create' %}",
            method: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            success: function(response) {
                console.log('Success:', response); // Debug log
                location.reload();
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseText); // Debug log
                alert('Error creating payment: ' + xhr.responseText);
            }
        });
    });


    // Delete checker
    $('.delete-checker').click(function() {
        if (confirm('Are you sure you want to delete this checker?')) {
            const checkerId = $(this).data('checker');
            $.ajax({
                url: `/testapp/checkers/${checkerId}/delete/`,
                method: 'POST',
                headers: {'X-CSRFToken': '{{ csrf_token }}'},
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert(xhr.responseJSON.error);
                }
            });
        }
    });
});
</script>
{% endblock %}
```

# testapp/templates/home.html

```html
{% extends 'base.html' %}

{% block title %}Home - MyProject{% endblock %}

{% block content %}
<h1>Welcome to MyProject!</h1>
<p>This is the home page.</p>
{% endblock %}

```

# testapp/templates/invoice/invoice_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Invoice{% endblock %}

{% block content %}
<h1>Delete Invoice</h1>
<p>Are you sure you want to delete the invoice with reference "{{ invoice.ref }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'invoice-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/invoice/invoice_form.html

```html
{% extends 'base.html' %}
{% load humanize %}
{% load accounting_filters %}


{% block title %}Invoice Form{% endblock %}

{% block content %}
<h1>{{ view.object.pk|default:'Add New Invoice' }}</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    {{ products.management_form }}

    <div style="display: none;">
        {% for product_form in products %}
            <div class="product-form">
                {{ product_form.id }}
                {{ product_form.product }}
                {{ product_form.quantity }}
                {{ product_form.unit_price }}
                {{ product_form.reduction_rate }}
                {{ product_form.vat_rate }}
                {% if product_form.instance.pk %}{{ product_form.DELETE }}{% endif %}
            </div>
        {% endfor %}
    </div>
    
    <button type="submit" class="btn btn-success mt-4">Save</button>
    <a href="{% url 'invoice-list' %}" class="btn btn-secondary mt-4">Cancel</a>
</form>

<!-- Add Product Button after Invoice is saved -->
{% if view.object.pk %}
    <button type="button" id="add-product" class="btn btn-primary mt-4" data-toggle="modal" data-target="#productModal">Add Product</button>

    <!-- Table to show all products linked to the current invoice -->
    <h3 class="mt-4">Products in Invoice</h3>
    <table class="table table-hover table-bordered mt-2">
        <thead class="thead-dark">
            <tr>
                <th>Product</th>
                <th>Fiscal Label</th>
                <th>Expense Code</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Reduction Rate (%)</th>
                <th>VAT Rate (%)</th>
                <th>Subtotal</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="product-list">
            {% for product in view.object.products.all %}
            <tr data-product-id="{{ product.pk }}">
                <td>{{ product.product.name }}</td>
                <td>{{ product.product.fiscal_label }}</td>
                <td>{{ product.product.expense_code }}</td> 
                <td>{{ product.quantity }}</td>
                <td>{{ product.unit_price|space_thousands }}</td>
                <td>{{ product.reduction_rate }}</td>
                <td>{{ product.vat_rate }}</td>
                <td>{{ product.subtotal|space_thousands }}</td>
                <td>
                    <button class="btn btn-warning btn-sm edit-product" data-product-id="{{ product.pk }}">Edit</button>
                    <button class="btn btn-danger btn-sm delete-product" data-product-id="{{ product.pk }}">Delete</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <th colspan="7" class="text-right">Raw Total:</th>
                <th id="raw-total">{{ view.object.raw_amount|space_thousands }}</th>
            </tr>
            <tr>
                <th colspan="7" class="text-right">Total Tax Amount:</th>
                <th id="tax-total">{{ view.object.total_tax_amount|space_thousands }}</th>
            </tr>
            <tr>
                <th colspan="7" class="text-right text-primary">Total Amount (Including Tax):</th>
                <th id="total-amount">{{ view.object.total_amount|space_thousands }}</th>
            </tr>
        </tfoot>
    </table>
    <!-- Accounting Summary -->
    <h3 class="mt-4">Accounting Summary</h3>
    <table class="table table-hover table-bordered mt-2 accounting-table">
        <thead class="thead-dark">
            <tr>
                <th class="align-middle">Date</th>
                <th class="align-middle label-column">Label</th>
                <th class="text-right align-middle">Debit</th>
                <th class="text-right align-middle">Credit</th>
                <th class="align-middle">Account Code</th>
                <th class="align-middle">Reference</th>
                <th class="align-middle">Journal</th>
                <th class="align-middle">Counterpart</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in view.object.get_accounting_entries %}
            <tr class="{% if entry.credit %}total-row font-weight-bold{% elif 'VAT' in entry.label %}vat-row{% endif %}">
                <td>{{ entry.date|date:"Y-m-d" }}</td>
                <td>{{ entry.label }}</td>
                <td class="text-right">
                    {% if entry.debit %}
                        {{ entry.debit|space_thousands }}
                    {% endif %}
                </td>
                <td class="text-right">
                    {% if entry.credit %}
                        {{ entry.credit|space_thousands }}
                    {% endif %}
                </td>
                <td>{{ entry.account_code }}</td>
                <td>{{ entry.reference }}</td>
                <td class="text-center">{{ entry.journal }}</td>
                <td>{{ entry.counterpart }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot class="bg-light">
            <tr class="font-weight-bold">
                <td colspan="2" class="text-right">Totals:</td>
                <td class="text-right">
                    {% with entries=view.object.get_accounting_entries %}
                        {{ entries|sum_debit|space_thousands }}
                    {% endwith %}
                </td>
                <td class="text-right">
                    {% with entries=view.object.get_accounting_entries %}
                        {{ entries|sum_credit|space_thousands }}
                    {% endwith %}
                </td>
                <td colspan="4"></td>
            </tr>
        </tfoot>
    </table>
{% else %}
    <div class="alert alert-warning mt-4">
        Save the invoice before adding products.
    </div>
{% endif %}

<!-- Modal Template for Adding Product -->
<div class="modal fade" id="productModal" tabindex="-1" role="dialog" aria-labelledby="productModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="productModalLabel">Add Product to Invoice</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <div id="modal-alert" class="alert d-none" role="alert"></div>
                <form id="add-product-form">
                    <div class="form-group">
                        <label for="product">Product:</label>
                        <input type="text" id="product" name="product" class="form-control" placeholder="Search for a product...">
                        <input type="hidden" id="product_id" name="product_id">
                        
                        <div id="new-product-fields" style="display: none;">
                            <input type="text" id="new-product-name" class="form-control mt-2" placeholder="New Product Name">
                            <input type="text" id="fiscal-label" class="form-control mt-2" placeholder="Fiscal Label">
                            <div class="custom-control custom-checkbox mt-2">
                                <input type="checkbox" class="custom-control-input" id="is-energy">
                                <label class="custom-control-label" for="is-energy">Is Energy Product</label>
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="expense_code">Expense Code:</label>
                        <input type="text" id="expense_code" name="expense_code" class="form-control" pattern="[0-9]{5,}" title="Expense code must be numeric and at least 5 characters long">
                    </div>
                    <div class="form-group">
                        <label for="quantity">Quantity:</label>
                        <input type="number" id="quantity" name="quantity" class="form-control" min="1">
                        <div class="invalid-feedback">
                            Please enter a valid quantity (minimum of 1).
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="unit_price">Unit Price:</label>
                        <input type="number" id="unit_price" name="unit_price" class="form-control" min="0.01" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="reduction_rate">Reduction Rate (%)</label>
                        <input type="number" id="reduction_rate" name="reduction_rate" class="form-control" min="0" max="100" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="vat_rate">VAT Rate (%):</label>
                        <select id="vat_rate" name="vat_rate" class="form-control">
                            <option value="0.00">0%</option>
                            <option value="7.00">7%</option>
                            <option value="10.00">10%</option>
                            <option value="11.00">11%</option>
                            <option value="14.00">14%</option>
                            <option value="16.00">16%</option>
                            <option value="20.00">20%</option>
                        </select>
                    </div>
                </form>
             </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" id="save-product-button" class="btn btn-primary">Save Product</button>
            </div>
        </div>
    </div>
</div>

<style>
    .ui-autocomplete {
        position: absolute;
        z-index: 2000;
        background-color: white;
        border: 1px solid #ccc;
        max-height: 200px;
        overflow-y: auto;
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .ui-menu-item {
        padding: 8px 12px;
        cursor: pointer;
    }
    
    .ui-menu-item:hover {
        background-color: #f8f9fa;
    }
</style>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        $('#productModal').on('hidden.bs.modal', function () {
        // Reset the form fields
        $('#add-product-form')[0].reset();

        // Remove validation styles
        $('#add-product-form .is-invalid').removeClass('is-invalid');

        // Remove error messages
        $('#add-product-form .invalid-feedback').remove();
    });

        $(document).ready(function() {
            $("#product").autocomplete({
            minLength: 2,
            source: function(request, response) {
                $.ajax({
                    url: "{% url 'product-autocomplete' %}",
                    dataType: "json",
                    data: { term: request.term },
                    success: function(data) {
                        response(data);
                    }
                });
            },

            select: function(event, ui) {
                $("#product").val(ui.item.label.split(' (')[0]);
                $("#product_id").val(ui.item.value);
                
                if (ui.item.value === 'new') {
                    $('#new-product-fields').show();
                    $('#expense_code').val('').prop('disabled', false);
                } else {
                    $('#new-product-fields').hide();
                    loadProductDetails(ui.item.value);
                }
                return false;
            }
        });
        
        // Test if element exists
        console.log("Product input element:", $("#product").length);
    });


        // Add this function to load product details
        function loadProductDetails(productId) {
            $.ajax({
                url: `/testapp/products/${productId}/details/`,  // You'll need to create this endpoint
                method: 'GET',
                success: function(data) {
                    $('#expense_code').val(data.expense_code).prop('disabled', true);
                    $('#vat_rate').val(data.vat_rate);
                },
                error: function() {
                    alert("Failed to load product details.");
                }
            });
}
        // Function to load products into dropdown
        function loadProducts(selectedProductId = null) {
        $.ajax({
            url: "{% url 'product-autocomplete' %}",
            method: "GET",
            success: function (data) {
                const productSelect = document.getElementById('product');
                productSelect.innerHTML = '<option value="">Select a Product</option>';
                productSelect.innerHTML += '<option value="new">+ Create New Product</option>';

                // Populate dropdown with products
                data.forEach(function (product) {
                    const option = document.createElement('option');
                    option.value = product.value;
                    option.text = product.label;
                    productSelect.appendChild(option);
                });

                // If a product ID is provided, select it
                if (selectedProductId) {
                    $('#product').val(selectedProductId);
                    $('#product').prop('disabled', true);
                    $('#new-product-fields').hide();
                } else {
                    $('#product').prop('disabled', false);
                }
            },
            error: function () {
                alert("Failed to load products.");
            }
        });
    }

        // Modal show event handler
        $('#productModal').on('show.bs.modal', function () {
            const editingProductId = $('#save-product-button').attr('data-editing');
            if (!editingProductId) {
                // Add mode - load all products
                loadProducts();
            }
        });

        // Save button click handler
        document.getElementById('save-product-button').addEventListener('click', function () {
            const productId = $('#save-product-button').attr('data-editing');
            const selectedProductId = $('#product_id').val();
            const quantity = $('#quantity').val();
            const unitPrice = $('#unit_price').val();
            const reductionRate = $('#reduction_rate').val();
            const vatRate = $('#vat_rate').val();
            const expenseCode = $('#expense_code').val();
            const isNewProduct = selectedProductId === 'new';

            // Validate fields before submission
            let isValid = true;
            let errorMessage = "";

            if (!productId && !selectedProductId) {  // Only validate product selection in add mode
                isValid = false;
                errorMessage += "Please select a product.\n";
            }
            if (quantity <= 0) {
                isValid = false;
                errorMessage += "Quantity must be a positive number.\n";
            }
            if (unitPrice <= 0) {
                isValid = false;
                errorMessage += "Unit Price must be a positive value.\n";
            }
            if (reductionRate < 0 || reductionRate > 100) {
                isValid = false;
                errorMessage += "Reduction Rate must be between 0 and 100.\n";
            }
            if (!/^\d{5,}$/.test(expenseCode)) {
                isValid = false;
                errorMessage += "Expense code must be numeric and at least 5 characters long.\n";
            }

            if (isNewProduct) {
                if (!$('#new-product-name').val()) {
                    isValid = false;
                    errorMessage += "Product name is required.\n";
                }
                if (!$('#fiscal-label').val()) {
                    isValid = false;
                    errorMessage += "Fiscal label is required.\n";
                }
            }

            if (!isValid) {
                alert(errorMessage);
                return;
            }

            // If creating a new product
            if (isNewProduct && !productId) {
                // First create the product
                const productData = {
                    name: $('#new-product-name').val(),
                    fiscal_label: $('#fiscal-label').val(),
                    is_energy: $('#is-energy').is(':checked'),
                    expense_code: expenseCode,
                    vat_rate: vatRate,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                };

                $.ajax({
                    url: "{% url 'product-ajax-create' %}",
                    method: "POST",
                    data: productData,
                    success: function(response) {
                        // Now create the invoice product with the new product ID
                        const requestData = {
                            quantity: quantity,
                            unit_price: unitPrice,
                            reduction_rate: reductionRate,
                            vat_rate: vatRate,
                            expense_code: expenseCode,
                            invoice_id: '{{ view.object.pk }}',
                            product: response.product_id,
                            csrfmiddlewaretoken: '{{ csrf_token }}'
                        };

                        $.ajax({
                            url: "{% url 'add-product-to-invoice' %}",
                            method: "POST",
                            data: requestData,
                            success: function(response) {
                                location.reload();
                            },
                            error: function(error) {
                                alert("Failed to add product to invoice.");
                                console.error(error);
                            }
                        });
                    },
                    error: function(error) {
                        alert("Failed to create new product.");
                        console.error(error);
                    }
                });
            } else {
                // Existing logic for editing or adding existing product
                const requestData = {
                    quantity: quantity,
                    unit_price: unitPrice,
                    reduction_rate: reductionRate,
                    vat_rate: vatRate,
                    expense_code: expenseCode,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                };

                if (!productId) {
                    // Add mode - include additional fields
                    requestData.invoice_id = '{{ view.object.pk }}';
                    requestData.product = selectedProductId;
                }

                // Make AJAX request
                $.ajax({
                    url: productId ? 
                        `/testapp/invoices/edit-product/${productId}/` : 
                        "{% url 'add-product-to-invoice' %}",
                    method: "POST",
                    data: requestData,
                    success: function (response) {
                        location.reload();
                    },
                    error: function (error) {
                        alert("Failed to save product. Please try again.");
                        console.error(error);
                    }
                });
            }
        });

        // Edit button click handler
        document.querySelectorAll('.edit-product').forEach(function (editButton) {
            editButton.addEventListener('click', function () {
                const productId = editButton.getAttribute('data-product-id');

                // Load product data into the modal for editing
                $.ajax({
                    url: `/testapp/invoices/edit-product/${productId}/`,
                    method: "GET",
                    success: function (data) {
                        // First load all products, then set the selected one
                        loadProducts(data.product);
                        
                        // Populate other fields
                        $('#product').val(data.product_name); // Add product_name to your EditProductInInvoiceView response
                        $('#product_id').val(data.product);
                        $('#productModalLabel').text('Edit Product in Invoice');
                        $('#quantity').val(data.quantity);
                        $('#unit_price').val(data.unit_price);
                        $('#reduction_rate').val(data.reduction_rate);
                        $('#vat_rate').val(data.vat_rate.toFixed(2)).prop('disabled', true);
                        $('#expense_code').val(data.expense_code).prop('disabled', true);

                        // Set editing mode
                        $('#save-product-button').attr('data-editing', productId);
                        $('#productModal').modal('show');
                    },
                    error: function (error) {
                        alert("Failed to load product data for editing.");
                    }
                });
            });
        });

        // Delete button click handler
        document.querySelectorAll('.delete-product').forEach(function (deleteButton) {
            deleteButton.addEventListener('click', function () {
                const productId = deleteButton.getAttribute('data-product-id');

                if (confirm("Are you sure you want to delete this product?")) {
                    $.ajax({
                        url: `/testapp/invoices/edit-product/${productId}/`,
                        method: "DELETE",
                        headers: {
                            'X-CSRFToken': '{{ csrf_token }}'
                        },
                        success: function (response) {
                            deleteButton.closest('tr').remove();
                        },
                        error: function (error) {
                            alert("Failed to delete product. Please try again.");
                        }
                    });
                }
            });
        });

        // Modal close handler
        $('#productModal').on('hidden.bs.modal', function () {
            $('#add-product-form')[0].reset();
            $('#save-product-button').removeAttr('data-editing');
            $('#productModalLabel').text('Add Product to Invoice');
            $('#product').prop('disabled', false);  // Re-enable product selection
            $('#new-product-fields').hide(); // Hide new product fields
            $('#expense_code').prop('disabled', false); // Reset expense code field
        });

        const form = document.getElementById("add-product-form");
        const alertBox = document.getElementById("modal-alert");

        document.getElementById("save-product-button").addEventListener("click", () => {
            // Clear previous alerts
            alertBox.classList.add("d-none");
            alertBox.innerHTML = "";

            // Reset validation states
            const inputs = form.querySelectorAll(".form-control");
            inputs.forEach((input) => {
                input.classList.remove("is-invalid");
            });

            // Validate fields
            let isValid = true;

            // Example validation: Quantity
            const quantity = document.getElementById("quantity");
            if (!quantity.value || quantity.value < 1) {
                isValid = false;
                quantity.classList.add("is-invalid");
                quantity.nextElementSibling.textContent = "Quantity must be at least 1.";
            }

            // Example validation: Expense Code
            const expenseCode = document.getElementById("expense_code");
            if (!quantity.value ||!/^[0-9]{5,}$/.test(expenseCode.value)) {
                isValid = false;
                expenseCode.classList.add("is-invalid");
                expenseCode.nextElementSibling.textContent =
                    "Expense code must be numeric and at least 5 characters long.";
            }

            if (isValid) {
                // Simulate form submission success
                alertBox.className = "alert alert-success";
                alertBox.textContent = "Product saved successfully!";
                alertBox.classList.remove("d-none");

                // Close modal after 2 seconds
                setTimeout(() => {
                    $("#productModal").modal("hide");
                }, 2000);
            } else {
                // Show error alert
                alertBox.className = "alert alert-danger";
                alertBox.textContent = "Please fix the errors in the form.";
                alertBox.classList.remove("d-none");
            }
        });
    });
</script>
{% endblock %}

```

# testapp/templates/invoice/invoice_list.html

```html
{% extends 'base.html' %}
{% load humanize %}

{% block title %}Invoice List{% endblock %}

{% block content %}
<script>
    console.log("Script block loaded");
    
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM loaded");
    
        // Initialize Select2
        try {
            $('#supplier-filter').select2({
                placeholder: 'Select supplier',
                allowClear: true,
                ajax: {
                    url: "{% url 'supplier-autocomplete' %}",
                    dataType: 'json',
                    delay: 250,
                    processResults: function(data) {
                        return {
                            results: data.map(item => ({
                                id: item.value,
                                text: item.label
                            }))
                        };
                    }
                }
            });
            console.log("Select2 initialized");
        } catch (e) {
            console.error("Error initializing Select2:", e);
        }
    
        // Filter functionality
        const applyButton = document.getElementById('apply-filters');
        if (applyButton) {
            applyButton.addEventListener('click', function(e) {
                e.preventDefault();
                // Debug: Log all form elements
                const form = document.getElementById('filter-form');
                console.log("All form elements:", form.elements);
                console.log("Apply button clicked");

                // Get all form values including checkboxes and select2
                const filters = {};
                
                // Get standard form inputs
                const formData = new FormData(document.getElementById('filter-form'));
                
                // Debug log
                console.log("Form data before processing:", Object.fromEntries(formData));

                // Process each form element
                $('#filter-form').find('input, select').each(function() {
                    const input = $(this);
                    const name = input.attr('name');
                    
                    if (!name) return; // Skip if no name attribute

                    if (input.is(':checkbox')) {
                        // Only add checked checkboxes
                        if (input.is(':checked')) {
                            filters[name] = input.val();
                        }
                    } else if (input.hasClass('select2-hidden-accessible')) {
                        // Handle Select2 inputs
                        const value = input.val();
                        if (value) {
                            filters[name] = value;
                        }
                    } else {
                        // Handle regular inputs
                        const value = input.val();
                        if (value) {
                            filters[name] = value;
                        }
                    }
                });

                // Debug logs
                console.log("Final filters object:", filters);
                
                // Apply filters
                const searchParams = new URLSearchParams(filters);
                window.location.search = searchParams.toString();
            });
        } else {
            console.error("Apply button not found");
        }
            // Update URL without refreshing page
            
        // Reset filters
        const resetButton = document.getElementById('reset-filters');
        if (resetButton) {
            resetButton.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Reset clicked");
                
                // Reset form
                document.getElementById('filter-form').reset();
                
                // Reset Select2 fields
                $('.select2-hidden-accessible').val(null).trigger('change');
                
                // Uncheck all checkboxes
                $('input[type="checkbox"]').prop('checked', false);
                
                // Clear URL parameters and reload
                window.history.pushState({}, '', `${window.location.pathname}?${urlParams.toString()}`);
            });
        }

        // Initialize filters from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        for (let [key, value] of urlParams.entries()) {
            const input = document.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value === '1';
                } else if ($(input).hasClass('select2-hidden-accessible')) {
                    // For Select2, we need to create the option and set it
                    const select2Input = $(input);
                    select2Input.append(new Option(value, value, true, true)).trigger('change');
                } else {
                    input.value = value;
                }
            }
        }

        // Debug log for URL parameters
        console.log("URL parameters:", Object.fromEntries(urlParams));
    
        // Show/hide filter panel
        $('#toggle-filters').click(function(e) {
            $('.filter-panel').slideToggle();
            $(this).find('i').toggleClass('fa-filter fa-filter-slash');
        });
    });
</script>
    
<h1>Invoice List</h1>
<a href="{% url 'invoice-create' %}" class="btn btn-primary">Add New Invoice</a>

<div class="filter-section mb-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <button class="btn btn-outline-secondary" id="toggle-filters">
            <i class="fas fa-filter"></i> Filters
            <span class="badge badge-primary ml-2 active-filters-count" style="display:none">0</span>
        </button>
        <div class="active-filters">
            <span class="results-count"></span>
        </div>
    </div>

    <div class="filter-panel card" {% if not active_filters %}style="display:none"{% endif %}>
        <div class="card-body">
            <form id="filter-form" class="row">
                <!-- Date Range Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Date Range</label>
                    <div class="input-group">
                        <input type="date" class="form-control" name="date_from" id="date-from">
                        <div class="input-group-prepend input-group-append">
                            <span class="input-group-text">to</span>
                        </div>
                        <input type="date" class="form-control" name="date_to" id="date-to">
                    </div>
                </div>

                <!-- Supplier Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Supplier</label>
                    <select class="form-control" name="supplier" id="supplier-filter">
                        <option value="">All Suppliers</option>
                    </select>
                </div>

                <!-- Payment Status Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Payment Status</label>
                    <select class="form-control" name="payment_status" id="payment-status">
                        <option value="">All</option>
                        <option value="not_paid">Not Paid</option>
                        <option value="partially_paid">Partially Paid</option>
                        <option value="paid">Paid</option>
                    </select>
                </div>

                <!-- Amount Range Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Amount Range</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="amount_min" id="amount-min" placeholder="Min">
                        <div class="input-group-prepend input-group-append">
                            <span class="input-group-text">to</span>
                        </div>
                        <input type="number" class="form-control" name="amount_max" id="amount-max" placeholder="Max">
                    </div>
                </div>

                <!-- Export Status Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Export Status</label>
                    <select class="form-control" name="export_status" id="export-status">
                        <option value="">All</option>
                        <option value="exported">Exported</option>
                        <option value="not_exported">Not Exported</option>
                    </select>
                </div>

                <!-- Document Type Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Document Type</label>
                    <select class="form-control" name="document_type" id="document-type">
                        <option value="">All</option>
                        <option value="invoice">Invoice</option>
                        <option value="credit_note">Credit Note</option>
                    </select>
                </div>
                
                
                <!-- Product Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Product</label>
                    <select class="form-control" name="product" id="product-filter">
                        <option value="">All Products</option>
                    </select>
                </div>
                
                <!-- Payment Status Checks -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Payment Checks</label>
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="pending-checks" name="has_pending_checks" value="1">
                        <label class="custom-control-label" for="pending-checks">Has Pending Checks</label>
                    </div>
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="delivered-unpaid" name="has_delivered_unpaid" value="1">
                        <label class="custom-control-label" for="delivered-unpaid">Has Delivered Unpaid Checks</label>
                    </div>
                </div>
                
                <!-- Energy Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="is-energy" name="is_energy" value="1">
                        <label class="custom-control-label" for="is-energy">Energy Supplier</label>
                    </div>
                </div>
                
                <!-- Credit Note Status -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Credit Note Status</label>
                    <select class="form-control" name="credit_note_status">
                        <option value="">All</option>
                        <option value="has_credit_notes">Has Credit Notes</option>
                        <option value="no_credit_notes">No Credit Notes</option>
                        <option value="partially_credited">Partially Credited</option>
                    </select>
                </div>
                
                <!-- Due Date Range -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <label>Due Date Range</label>
                    <div class="input-group">
                        <input type="date" class="form-control" name="due_date_from">
                        <div class="input-group-prepend input-group-append">
                            <span class="input-group-text">to</span>
                        </div>
                        <input type="date" class="form-control" name="due_date_to">
                    </div>
                </div>

                <!-- Overdue Filter -->
                <div class="col-md-6 col-lg-3 mb-3">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="is-overdue" name="is_overdue" value="1">
                        <label class="custom-control-label" for="is-overdue">Overdue Invoices</label>
                    </div>
                </div>
                <div class="active-filters-tags">
                    <!-- Active filter tags will be inserted here -->
                </div>
             <div class="d-flex justify-content-between mt-3">
                 <div>
                     <button class="btn btn-primary" id="apply-filters">
                        <i class="fas fa-check"></i> Apply Filters Not Working
                    </button>
                    <button class="btn btn-secondary ml-2" id="reset-filters">
                        <i class="fas fa-times"></i> Reset
                    </button>
                </div>
            </div>
            <div class="col-12">  <!-- Add this wrapper div -->
                <button type="button" id="apply-filters" class="btn btn-primary">
                    Apply Filters Working !
                </button>
            </div>
        </form>
        </div>
    </div>
</div>

<div class="table-responsive" id="invoice-table-wrapper">
    <table class="table mt-4 table-hover">
        <thead>
            <tr>
                <th>Export</th>
                <th>Date</th>
                <th>Reference</th>
                <th>Supplier</th>
                <th>Fiscal Label</th>
                <th>Raw Amount</th>
                <th>Tax Rate (%)</th>
                <th>Tax Amount</th>
                <th>Total Amount (Incl. Tax)</th>
                <th>Status</th>
                <th>Actions</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {% for invoice in invoices %}
                {% if invoice.type == 'invoice' %}
                    <tr class="{% if invoice.payment_status == 'paid' %}table-success{% elif invoice.exported_at %}table-light{% endif %}">
                        <td>
                            {% if invoice.exported_at %}
                                <span class="text-muted">
                                    Exported {{ invoice.exported_at|date:"d-m-Y" }}
                                    <button type="button" 
                                            class="btn btn-warning btn-sm unexport-btn ml-2" 
                                            data-invoice-id="{{ invoice.id }}">
                                        <i class="fas fa-undo"></i>
                                    </button>
                                </span>
                            {% else %}
                                <input type="checkbox" 
                                    name="invoice_ids" 
                                    value="{{ invoice.id }}" 
                                    class="export-checkbox"
                                    {% if invoice.payment_status == 'paid' %}disabled{% endif %}>
                            {% endif %}
                        </td>
                                <td>{{ invoice.date }}</td>
                                <td>{{ invoice.ref }}</td>
                                <td>{{ invoice.supplier.name }}</td>
                                <td>{{ invoice.fiscal_label }}</td>
                                <td>{{ invoice.raw_amount|floatformat:2|intcomma }}</td>
                                <td>
                                    {% with invoice.products.all|length as product_count %}
                                        {% for product in invoice.products.all %}
                                            {{ product.vat_rate }}{% if not forloop.last %}, {% endif %}
                                        {% endfor %}
                                    {% endwith %}
                                </td>
                                <td>
                                    {% if invoice.total_tax_amount %}
                                        {{ invoice.total_tax_amount|floatformat:2|intcomma }}
                                    {% else %}
                                        <strong>Tax Missing</strong>
                                    {% endif %}
                                </td>                
                                <td class="text-right">
                                    {{ invoice.total_amount|floatformat:2|intcomma }}
                                    {% if invoice.credit_notes.exists %}
                                        <br>
                                        <small class="text-muted">
                                            Net: {{ invoice.net_amount|floatformat:2|intcomma }}
                                        </small>
                                        <button class="btn btn-link btn-sm p-0 ml-1 toggle-credit-notes" 
                                                data-invoice="{{ invoice.id }}">
                                            <i class="fas fa-receipt"></i>
                                        </button>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if invoice.payment_status == 'paid' %}
                                        <span class="badge badge-success">
                                            <i class="fas fa-lock"></i> Paid
                                        </span>
                                    {% else %}
                                        {% if invoice.credit_notes.exists %}
                                            <span class="badge badge-info">
                                                Partially Credited
                                                <small>({{ invoice.credit_notes.count }} note{{ invoice.credit_notes.count|pluralize }})</small>
                                            </span>
                                        {% endif %}
                                        <span class="badge {% if invoice.payment_status == 'partially_paid' %}badge-warning{% else %}badge-danger{% endif %}">
                                            {% if invoice.payment_status == 'partially_paid' %}
                                                Partially Paid 
                                                <small>({{ invoice.payments_summary.percentage_paid|floatformat:1 }}%)</small>
                                            {% else %}
                                                Not Paid
                                            {% endif %}
                                        </span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if not invoice.payment_status == 'paid' %}
                                        <a href="{% url 'invoice-update' invoice.pk %}" 
                                        class="btn btn-warning {% if invoice.exported_at %}disabled{% endif %}">
                                            <i class="fas fa-edit"></i> Edit
                                        </a>
                                        <a href="{% url 'invoice-delete' invoice.pk %}" 
                                        class="btn btn-danger {% if invoice.exported_at %}disabled{% endif %}">
                                            Delete
                                        </a>
                                        <button class="btn btn-info btn-sm" 
                                                data-toggle="modal" 
                                                data-target="#creditNoteModal" 
                                                data-invoice-id="{{ invoice.id }}"
                                                {% if not invoice.can_be_credited %}disabled{% endif %}>
                                            <i class="fas fa-reply"></i> Credit Note
                                        </button>
                                    {% else %}
                                        <button class="btn btn-secondary" disabled>
                                            <i class="fas fa-lock"></i> Paid
                                        </button>
                                    {% endif %}
                                </td>
                                <td>
                                    <button class="btn btn-info" data-toggle="modal" data-target="#invoiceDetailsModal" data-invoice="{{ invoice.pk }}">Details</button>
                                    <button class="btn btn-info btn-sm"                             
                                            data-toggle="modal" 
                                            data-target="#paymentDetailsModal"
                                            data-invoice="{{ invoice.pk }}">
                                        Payment Details
                                    </button>
                                    <button class="btn btn-info btn-sm accounting-summary-btn" 
                                            data-invoice-id="{{ invoice.id }}" 
                                            title="Show Accounting Summary">
                                        <i class="fas fa-book"></i>
                                    </button>
                                </td>
                            </tr>
                        </tr>
                    {% if invoice.credit_notes.exists %}
                        <tr class="credit-notes-row d-none bg-light" data-parent="{{ invoice.id }}">
                            <td colspan="12">
                                <div class="ml-4">
                                    <h6 class="mb-3">
                                        <i class="fas fa-receipt"></i> 
                                        Credit Notes for Invoice {{ invoice.ref }}
                                    </h6>
                                    <table class="table table-sm">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Date</th>
                                                <th>Reference</th>
                                                <th>Products</th>
                                                <th class="text-right">Amount</th>
                                                <th>Status</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for credit_note in invoice.credit_notes.all %}
                                                <tr>
                                                    <td>{{ credit_note.date|date:"Y-m-d" }}</td>
                                                    <td>{{ credit_note.ref }}</td>
                                                    <td>
                                                        {% for product in credit_note.products.all %}
                                                            {{ product.product.name }} ({{ product.quantity }})
                                                            {% if not forloop.last %}, {% endif %}
                                                        {% endfor %}
                                                    </td>
                                                    <td class="text-right text-danger">
                                                        -{{ credit_note.total_amount|floatformat:2|intcomma }}
                                                    </td>
                                                    <td>
                                                        <span class="badge badge-info">
                                                            <i class="fas fa-receipt"></i> Credit Note
                                                        </span>
                                                        {% if credit_note.exported_at %}
                                                            <span class="badge badge-secondary">
                                                                <i class="fas fa-file-export"></i> Exported
                                                            </span>
                                                        {% endif %}
                                                    </td>
                                                    <td>
                                                        <button class="btn btn-sm btn-info"
                                                                data-toggle="modal" 
                                                                data-target="#invoiceDetailsModal" 
                                                                data-invoice="{{ credit_note.id }}">
                                                            <i class="fas fa-info-circle"></i> Details
                                                        </button>
                                                    </td>
                                                </tr>
                                            {% endfor %}
                                            <tr class="font-weight-bold">
                                                <td colspan="3" class="text-right">Net Balance:</td>
                                                <td class="text-right">{{ invoice.net_amount|floatformat:2|intcomma }}</td>
                                                <td colspan="2"></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </td>
                        </tr>
                    {% endif %}

                {% endif %}

            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Export Button -->
<div class="d-flex justify-content-end mt-3">
    <button type="button" 
            id="export-selected" 
            class="btn btn-primary" 
            disabled>
        Export Selected
    </button>
</div>

<!-- Modal Template for Invoice Details -->
<div class="modal fade" id="invoiceDetailsModal" tabindex="-1" role="dialog" aria-labelledby="invoiceDetailsModalLabel">
    <div class="modal-dialog modal-lg" role="document"> <!-- Added modal-lg for larger modal -->
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="invoiceDetailsModalLabel">Invoice Details</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body modal-scrollable-content">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Unit Price</th>
                            <th>Quantity</th>
                            <th>VAT Rate</th>
                            <th>Reduction Rate</th>
                            <th>Raw Price</th>
                        </tr>
                    </thead>
                    <tbody id="invoice-details-table">
                        <!-- Filled by JavaScript -->
                    </tbody>
                </table>
                <div id="vat-summary"></div>
                <div id="total-amount-summary"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- Payment Details Modal -->
<div class="modal fade" id="paymentDetailsModal">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Payment Details</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <!-- Summary Cards -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Due</h6>
                                <h4 id="amount-due" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount Paid</h6>
                                <h4 id="amount-paid" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Amount to Issue</h6>
                                <h4 id="amount-to-issue" class="card-title"></h4>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="progress mb-4" style="height: 25px;">
                    <div id="payment-progress" 
                         class="progress-bar" 
                         role="progressbar" 
                         style="width: 0%"></div>
                </div>

                <!-- Detailed Breakdown -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <p class="mb-1">Pending Payments:</p>
                        <h5 id="pending-amount"></h5>
                    </div>
                    <div class="col-md-4">
                        <p class="mb-1">Delivered Payments:</p>
                        <h5 id="delivered-amount"></h5>
                    </div>
                    <div class="col-md-4">
                        <p class="mb-1">Remaining to Pay:</p>
                        <h5 id="remaining-amount"></h5>
                    </div>
                </div>

                <!-- Checks Table -->
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Reference</th>
                                <th>Amount</th>
                                <th>Created</th>
                                <th>Delivered</th>
                                <th>Paid</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="payment-checks-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Credit Note Modal -->
<div class="modal fade" id="creditNoteModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Create Credit Note</h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <!-- Credit Note Info -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <label for="credit-note-ref">Credit Note Reference *</label>
                        <input type="text" id="credit-note-ref" class="form-control" required>
                    </div>
                    <div class="col-md-6">
                        <label for="credit-note-date">Date *</label>
                        <input type="date" id="credit-note-date" class="form-control" required>
                    </div>
                </div>

                <!-- Original Invoice Info -->
                <div class="card mb-4">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Original Invoice</h6>
                                <div id="original-invoice-details"></div>
                            </div>
                            <div class="col-md-6">
                                <h6>Net Balance After Credit</h6>
                                <div id="net-balance-details"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Products Selection -->
                <form id="credit-note-form">
                    <input type="hidden" id="original-invoice-id">
                    <table class="table" id="products-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Original Qty</th>
                                <th>Already Credited</th>
                                <th>Available</th>
                                <th>Credit Qty</th>
                                <th>Unit Price</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                        <tfoot>
                            <tr>
                                <th colspan="6" class="text-right">Total Credit Amount:</th>
                                <th class="text-right" id="total-credit-amount">0.00</th>
                            </tr>
                        </tfoot>
                    </table>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="save-credit-note">Create Credit Note</button>
            </div>
        </div>
    </div>
</div>

<!-- Accounting Summary Modal -->
<div class="modal fade" id="accountingSummaryModal" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-book"></i> Accounting Summary
                </h5>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="accordion" id="accountingEntries">
                    <!-- Original Invoice Section -->
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0">Original Invoice Entries</h6>
                        </div>
                        <div class="card-body p-0">
                            <table class="table table-striped mb-0">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Account</th>
                                        <th>Label</th>
                                        <th class="text-right">Debit</th>
                                        <th class="text-right">Credit</th>
                                        <th>Reference</th>
                                        <th>Journal</th>
                                    </tr>
                                </thead>
                                <tbody id="originalEntries"></tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Credit Notes Section (shown only if exists) -->
                    <div id="creditNotesSection" class="card mt-3 d-none">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0">Credit Note Entries</h6>
                        </div>
                        <div class="card-body p-0">
                            <table class="table table-striped mb-0">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Account</th>
                                        <th>Label</th>
                                        <th class="text-right">Debit</th>
                                        <th class="text-right">Credit</th>
                                        <th>Reference</th>
                                        <th>Journal</th>
                                    </tr>
                                </thead>
                                <tbody id="creditNoteEntries"></tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Net Effect Section -->
                    <div class="card mt-3">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0">Net Effect</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <h6>Original Amount</h6>
                                    <p id="originalTotal" class="h4"></p>
                                </div>
                                <div class="col-md-4">
                                    <h6>Credit Notes</h6>
                                    <p id="creditTotal" class="h4 text-danger"></p>
                                </div>
                                <div class="col-md-4">
                                    <h6>Net Amount</h6>
                                    <p id="netTotal" class="h4 font-weight-bold"></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>


<!-- JavaScript time!!! -->
<script>

    // 1. Utility Functions - These are used throughout the code
    const Utils = {
        formatMoney: function(amount) {
            return new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'MAD',
                minimumFractionDigits: 2
            }).format(amount);
        },
        
        getProgressBarClass: function(percentage) {
            if (percentage >= 100) return 'bg-success';
            if (percentage > 50) return 'bg-warning';
            return 'bg-danger';
        },
        
        getStatusBadgeClass: function(status) {
            return {
                'pending': 'secondary',
                'delivered': 'warning',
                'paid': 'success',
                'cancelled': 'danger'
            }[status] || 'secondary';
        },
        
        formatStatus: function(status) {
            return status.charAt(0).toUpperCase() + status.slice(1);
        }
    };

    // 2. Modal Handlers - All modal-related functions
    const ModalHandlers = {
        // Invoice Details Modal
        loadInvoiceDetails: function(invoiceId) {
            $.ajax({
                url: "{% url 'invoice-details' %}",
                data: { 'invoice_id': invoiceId },
                success: function(data) {
                    $('#invoice-details-table').empty();
                    data.products.forEach(product => {
                        $('#invoice-details-table').append(`
                            <tr>
                                <td>${product.name}</td>
                                <td>${product.unit_price}</td>
                                <td>${product.quantity}</td>
                                <td>${product.vat_rate}</td>
                                <td>${product.reduction_rate}</td>
                                <td>${product.raw_price}</td>
                            </tr>
                        `);
                    });
                    
                    $('#vat-summary').empty();
                    data.vat_subtotals.forEach(vatSubtotal => {
                        $('#vat-summary').append(
                            `<p><strong>Subtotal for VAT ${vatSubtotal.vat_rate}:</strong> ${vatSubtotal.subtotal}</p>`
                        );
                    });
                    
                    $('#total-amount-summary').html(`
                        <strong>Total Raw Amount:</strong> ${data.total_raw_amount}<br>
                        <strong>Total VAT Amount:</strong> ${data.total_vat}<br>
                        <strong>Total Amount (Including Tax):</strong> ${data.total_amount}
                    `);
                }
            });
        },

        // Payment Details Modal
        loadPaymentDetails: function(invoiceId) {
            $.get(`/testapp/invoices/${invoiceId}/payment-details/`, function(data) {
                const details = data.payment_details;
                $('#amount-due').text(Utils.formatMoney(details.total_amount));
                $('#amount-paid').text(Utils.formatMoney(details.paid_amount));
                $('#amount-to-issue').text(Utils.formatMoney(details.amount_to_issue));

                const progressBar = $('#payment-progress');
                progressBar
                    .css('width', `${details.payment_percentage}%`)
                    .text(`${details.payment_percentage.toFixed(1)}%`)
                    .removeClass('bg-success bg-warning bg-danger')
                    .addClass(Utils.getProgressBarClass(details.payment_percentage));

                $('#pending-amount').text(Utils.formatMoney(details.pending_amount));
                $('#delivered-amount').text(Utils.formatMoney(details.delivered_amount));
                $('#remaining-amount').text(Utils.formatMoney(details.remaining_to_pay));

                ModalHandlers.updateChecksTable(data.checks);
            });
        },

        updateChecksTable: function(checks) {
            const tbody = $('#payment-checks-tbody');
            tbody.empty();

            checks.forEach(check => {
                tbody.append(`
                    <tr>
                        <td>${check.reference}</td>
                        <td>${Utils.formatMoney(check.amount)}</td>
                        <td>${check.created_at}</td>
                        <td>${check.delivered_at || '-'}</td>
                        <td>${check.paid_at || '-'}</td>
                        <td>
                            <span class="badge badge-${Utils.getStatusBadgeClass(check.status)}">
                                ${Utils.formatStatus(check.status)}
                            </span>
                        </td>
                    </tr>
                `);
            });
        },

        showAccountingSummary: function(invoiceId) {
            $.ajax({
                url: `/testapp/invoices/${invoiceId}/accounting-summary/`,
                method: 'GET',
                success: function(data) {
                    // Populate the modal
                    $('#originalEntries').empty();
                    data.original_entries.forEach(entry => {
                        $('#originalEntries').append(ModalHandlers.createAccountingRow(entry));
                    });

                    if (data.credit_note_entries.length > 0) {
                        $('#creditNotesSection').removeClass('d-none');
                        $('#creditNoteEntries').empty();
                        data.credit_note_entries.forEach(entry => {
                            $('#creditNoteEntries').append(ModalHandlers.createAccountingRow(entry));
                        });
                    } else {
                        $('#creditNotesSection').addClass('d-none');
                    }

                    $('#originalTotal').text(Utils.formatMoney(data.totals.original));
                    $('#creditTotal').text(Utils.formatMoney(data.totals.credit_notes));
                    $('#netTotal').text(Utils.formatMoney(data.totals.net));

                    $('#accountingSummaryModal').modal('show');
                },
                error: function(xhr) {
                    alert('Failed to load accounting summary: ' + xhr.responseText);
                }
            });
        },

        createAccountingRow: function(entry) {
            return `
                <tr>
                    <td>${entry.date}</td>
                    <td>${entry.account_code}</td>
                    <td>${entry.label}</td>
                    <td class="text-right">${entry.debit ? Utils.formatMoney(entry.debit) : ''}</td>
                    <td class="text-right">${entry.credit ? Utils.formatMoney(entry.credit) : ''}</td>
                    <td>${entry.reference}</td>
                    <td>${entry.journal}</td>
                </tr>
            `;
        }

    };

    // 3. Credit Note Handlers
    const CreditNoteHandlers = {
        // Store the initial net amount for calculations
        initialNetAmount: 0,

        initializeQuantityHandlers: function() {
            $('.credit-quantity').on('input', function() {
                const quantity = parseFloat($(this).val()) || 0;
                const available = parseFloat($(this).data('available'));
                
                if (quantity > available) {
                    $(this).val(available);
                    return;
                }
                
                CreditNoteHandlers.updateSubtotalsAndTotal();
            });
        },

        updateNetBalance: function(creditAmount) {
            $('#net-balance-details').html(`
                <p><strong>Original Amount:</strong> ${Utils.formatMoney(this.initialNetAmount)}</p>
                <p><strong>Credit Amount:</strong> ${Utils.formatMoney(creditAmount)}</p>
                <p class="font-weight-bold">Net Balance: ${Utils.formatMoney(this.initialNetAmount - creditAmount)}</p>
            `);
        },

        updateSubtotalsAndTotal: function() {
            let total = 0;
            $('.credit-quantity').each(function() {
                const quantity = parseFloat($(this).val()) || 0;
                const unitPrice = parseFloat($(this).data('unit-price'));
                const subtotal = quantity * unitPrice;
                
                $(this).closest('tr').find('.subtotal').text(Utils.formatMoney(subtotal));
                total += subtotal;
            });

            $('#total-credit-amount').text(Utils.formatMoney(total));
            this.updateNetBalance(total);
        },

        saveCreditNote: function() {
            if (!$('#credit-note-ref').val()) {
                alert('Please enter a credit note reference');
                return;
            }

            const products = [];
            $('.credit-quantity').each(function() {
                const quantity = parseFloat($(this).val()) || 0;
                if (quantity > 0) {
                    products.push({
                        product_id: $(this).data('product-id'),
                        quantity: quantity
                    });
                }
            });
            
            if (products.length === 0) {
                alert('Please select at least one product to credit');
                return;
            }

            $.ajax({
                url: '/testapp/invoices/create-credit-note/',
                method: 'POST',
                data: JSON.stringify({
                    original_invoice_id: $('#original-invoice-id').val(),
                    ref: $('#credit-note-ref').val(),
                    date: $('#credit-note-date').val(),
                    products: products
                }),
                contentType: 'application/json',
                success: function(response) {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error creating credit note: ' + xhr.responseText);
                }
            });
        }
    };

    // 4. Filter Handlers
    const FilterHandlers = {
        updateActiveFilters: function() {
            const activeFilters = [];
            const filterLabels = {
                date_from: 'From',
                date_to: 'To',
                supplier: 'Supplier',
                payment_status: 'Payment Status',
                amount_min: 'Min Amount',
                amount_max: 'Max Amount',
                export_status: 'Export Status',
                document_type: 'Document Type'
            };

            // Build URL parameters
            const urlParams = new URLSearchParams();
            
            $('#filter-form').serializeArray().forEach(function(item) {
                if (item.value) {
                    urlParams.append(item.name, item.value);
                    activeFilters.push({
                        name: filterLabels[item.name],
                        value: item.value,
                        param: item.name
                    });
                }
            });



            // Update filter count badge
            const filterCount = activeFilters.length;
            const countBadge = $('.active-filters-count');
            if (filterCount > 0) {
                countBadge.text(filterCount).show();
            } else {
                countBadge.hide();
            }

            // Update filter tags
            const tagsHtml = activeFilters.map(filter => `
                <span class="badge badge-info mr-2">
                    ${filter.name}: ${filter.value}
                    <button type="button" class="close ml-1" 
                            data-param="${filter.param}" 
                            aria-label="Remove filter">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </span>
            `).join('');

            $('.active-filters-tags').html(tagsHtml);
        },

        applyFilters: function() {
            const filters = {};
            const formData = $('#filter-form').serializeArray();
            console.log("Form data being submitted:", formData); // Debug log

            $('#filter-form').serializeArray().forEach(function(item) {
                if (item.value) {
                    filters[item.name] = item.value;
                }
            });

            console.log("Final filters object:", filters); // Debug log
            window.location.search = new URLSearchParams(filters).toString();
        },

        resetFilters: function() {
            $('#filter-form')[0].reset();
            $('#supplier-filter').val(null).trigger('change');
            window.location.search = '';
        }
    };

    
    document.addEventListener('DOMContentLoaded', function () {

    // Initialize Modal Events

 // Accounting summary button handler
 $(document).on('click', '.accounting-summary-btn', function() {
        const invoiceId = $(this).data('invoice-id');
        if (!invoiceId) {
            alert('Invoice ID is missing.');
            return;
        }
        ModalHandlers.showAccountingSummary(invoiceId);
    });

    // Credit note toggle handler
    $('.toggle-credit-notes').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const invoiceId = $(this).data('invoice');
        const icon = $(this).find('i');
        const creditNotesRow = $(`.credit-notes-row[data-parent="${invoiceId}"]`);
        
        creditNotesRow.toggleClass('d-none');
        icon.toggleClass('fa-receipt fa-times-circle');
    });

    // Make sure toggle works for dynamically loaded content
    $(document).on('click', '.toggle-credit-notes', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const invoiceId = $(this).data('invoice');
        const icon = $(this).find('i');
        const creditNotesRow = $(`.credit-notes-row[data-parent="${invoiceId}"]`);
        
        creditNotesRow.toggleClass('d-none');
        icon.toggleClass('fa-receipt fa-times-circle');
    });



    $('#invoiceDetailsModal').on('show.bs.modal', function(event) {
        const invoiceId = $(event.relatedTarget).data('invoice');
        ModalHandlers.loadInvoiceDetails(invoiceId);
    });

    $('#paymentDetailsModal').on('show.bs.modal', function(event) {
        const invoiceId = $(event.relatedTarget).data('invoice');
        ModalHandlers.loadPaymentDetails(invoiceId);
    });

    // Initialize Credit Note Events
    $('#creditNoteModal').on('show.bs.modal', function(event) {
        const invoiceId = $(event.relatedTarget).data('invoice-id');
        if (!invoiceId) {
            console.error('No Invoice ID found!');
            return;
        }

        $('#original-invoice-id').val(invoiceId);
        $('#credit-note-date').val(new Date().toISOString().split('T')[0]);

        $.ajax({
            url: `/testapp/invoices/${invoiceId}/credit-note-details/`,
            method: 'GET',
            success: function(data) {
                // Store initial net amount
                CreditNoteHandlers.initialNetAmount = data.invoice.total_amount - data.invoice.credited_amount;
                
                // Update UI
                $('#original-invoice-details').html(`
                    <p><strong>Reference:</strong> ${data.invoice.ref}</p>
                    <p><strong>Date:</strong> ${data.invoice.date}</p>
                    <p data-amount="${data.invoice.total_amount}">
                        <strong>Total Amount:</strong> ${Utils.formatMoney(data.invoice.total_amount)}
                    </p>
                    <p><strong>Already Credited:</strong> ${Utils.formatMoney(data.invoice.credited_amount)}</p>
                `);

                CreditNoteHandlers.updateNetBalance(0);

                // Populate products table
                const tbody = $('#products-table tbody').empty();
                data.products.forEach(product => {
                    tbody.append(`
                        <tr>
                            <td>${product.name}</td>
                            <td class="text-right">${product.original_quantity}</td>
                            <td class="text-right">${product.credited_quantity}</td>
                            <td class="text-right">${product.available_quantity}</td>
                            <td>
                                <input type="number" class="form-control form-control-sm credit-quantity"
                                    data-product-id="${product.id}"
                                    data-unit-price="${product.unit_price}"
                                    data-available="${product.available_quantity}"
                                    min="0" max="${product.available_quantity}" value="0">
                            </td>
                            <td class="text-right">${Utils.formatMoney(product.unit_price)}</td>
                            <td class="text-right subtotal">0.00</td>
                        </tr>
                    `);
                });

                CreditNoteHandlers.initializeQuantityHandlers();
            }
        });
    });

    $('#save-credit-note').on('click', function() {
        console.log("Save button clicked"); // Debug log
        CreditNoteHandlers.saveCreditNote();
    });

    // Export functionality
    const checkboxes = document.querySelectorAll('.export-checkbox');
    const exportButton = document.getElementById('export-selected');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('click', function() {
            const checkedBoxes = document.querySelectorAll('.export-checkbox:checked');
            exportButton.disabled = checkedBoxes.length === 0;
            console.log('Checked boxes:', checkedBoxes.length);
        });
    });

    exportButton.addEventListener('click', function() {
        const selectedIds = [...checkboxes]
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedIds.length === 0) return;

        fetch('{% url "export-invoices" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'  // Add CSRF token
            },
            body: JSON.stringify({invoice_ids: selectedIds})
        })
        .then(response => {
            if (response.ok) return response.blob();
            throw new Error('Export failed');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `accounting_export_${new Date().toISOString().slice(0,19).replace(/[:-]/g, '')}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            location.reload();
        })
        .catch(error => {
            alert('Failed to export invoices: ' + error.message);
        });
    });

    // Unexport functionality
    const unexportButtons = document.querySelectorAll('.unexport-btn');
    unexportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const invoiceId = this.dataset.invoiceId;
            
            if (!confirm('Are you sure you want to unexport this invoice?')) return;

            fetch(`/testapp/invoices/${invoiceId}/unexport/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'  // Add CSRF token
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Unexport failed');
                location.reload();
            })
            .catch(error => {
                alert('Failed to unexport invoice: ' + error.message);
            });
        });
    });

    // Initialize Filter Events


    $('#supplier-filter').select2({
        placeholder: 'Select supplier',
        allowClear: true,
        ajax: {
            url: '/testapp/suppliers/autocomplete/',
            dataType: 'json',
            delay: 250,
            processResults: function(data) {
                return {
                    results: data.map(item => ({
                        id: item.value,
                        text: item.label
                    }))
                };
            }
        }
    });

    $('#product-filter').select2({
        placeholder: 'Select product',
        allowClear: true,
        ajax: {
            url: "{% url 'product-autocomplete' %}",
            dataType: 'json',
            delay: 250,
            processResults: function(data) {
                return {
                    results: data.map(item => ({
                        id: item.value,
                        text: item.label
                    }))
                };
            }
        }
    });

    // Connect filter handlers to buttons
    $('#apply-filters').on('click', function(e) {
            e.preventDefault();
            console.log("Apply filters clicked");  // Debug log
            
            const filters = {};
            const formData = $('#filter-form').serializeArray();
            console.log("Form data:", formData);  // Debug log
            
            formData.forEach(function(item) {
                if (item.value) {
                    filters[item.name] = item.value;
                }
            });
            
            console.log("Filters to apply:", filters);  // Debug log
            window.location.search = new URLSearchParams(filters).toString();
        });

        $('#reset-filters').on('click', function(e) {
            e.preventDefault();
            console.log("Reset filters clicked");  // Debug log
            $('#filter-form')[0].reset();
            $('#supplier-filter').val(null).trigger('change');
            window.location.search = '';
        });
        
    // Remove individual filters
    $(document).on('click', '.active-filters-tags .close', function() {
        const param = $(this).data('param');
        $(`[name="${param}"]`).val('').trigger('change');
        FilterHandlers.applyFilters();
    });

    
    
    // Initialize autocomplete for existing forms
    document.querySelectorAll('.product-form').forEach(addAutocomplete);
    
});
       
</script>

{% endblock %}

```

# testapp/templates/invoice/partials/invoice_table.html

```html
<!-- templates/invoice/partials/invoice_table.html -->
<table class="table mt-4 table-hover">
    <thead>
        <tr>
            <th>Export</th>
            <th>Date</th>
            <th>Reference</th>
            <th>Supplier</th>
            <th>Fiscal Label</th>
            <th>Raw Amount</th>
            <th>Tax Rate (%)</th>
            <th>Tax Amount</th>
            <th>Total Amount (Incl. Tax)</th>
            <th>Status</th>
            <th>Actions</th>
            <th>Details</th>
        </tr>
    </thead>
    <tbody>
        {% for invoice in invoices %}
            <!-- Your existing invoice row template here -->
        {% empty %}
            <tr>
                <td colspan="12" class="text-center">
                    <div class="p-4">
                        <i class="fas fa-search fa-2x text-muted mb-3"></i>
                        <p class="mb-0">No invoices found matching your filters</p>
                        <button class="btn btn-link" id="reset-filters">Clear all filters</button>
                    </div>
                </td>
            </tr>
        {% endfor %}
    </tbody>
</table>
```

# testapp/templates/login.html

```html
{% extends 'base.html' %}

{% block title %}Login - MyProject{% endblock %}

{% block content %}
<div class="container">
    <h2>Login</h2>
    <form method="post">
        {% csrf_token %}
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary">Login</button>
    </form>
</div>
{% endblock %}

```

# testapp/templates/product/product_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Product{% endblock %}

{% block content %}
<h1>Delete Product</h1>
<p>Are you sure you want to delete "{{ product.name }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/product/product_form.html

```html
{% extends 'base.html' %}

{% block title %}Product Form{% endblock %}

{% block content %}
<h1>{{ view.object.name|default:'Add New Product' }}</h1>
<form method="post">
    {% csrf_token %}
    {% for field in form %}
        {% if field.name == 'vat_rate' %}
            <div class="form-group">
                <label>{{ field.label }}</label>
                <select name="{{ field.name }}" class="form-control auto-size-select">
                    {% for choice in field.field.choices %}
                        <option value="{{ choice.0 }}" {% if field.value|floatformat:2 == choice.0|floatformat:2 %}selected{% endif %}>
                            {{ choice.1 }}
                        </option>
                    {% endfor %}
                </select>
            </div>
        {% else %}
            <div class="form-group">
                {{ field.label_tag }}
                {{ field }}
            </div>
        {% endif %}
    {% endfor %}
    <button type="submit" class="btn btn-success">Save</button>
    <a href="{% url 'product-list' %}" class="btn btn-secondary">Cancel</a>
</form>

<style>
    .auto-size-select {
        display: inline-block;
        min-width: 100px; /* Set a reasonable minimum width */
        max-width: 100%; /* Ensure it doesn't exceed the container width */
        width: auto; /* Automatically adjust to content */
    }
</style>

<script>
    document.querySelectorAll('.auto-size-select').forEach(select => {
        select.style.width = `${select.scrollWidth}px`;
    });
</script>


{% endblock %}

```

# testapp/templates/product/product_list.html

```html
{% extends 'base.html' %}

{% block title %}Product List{% endblock %}

{% block content %}
<h1>Product List</h1>
<a href="{% url 'product-create' %}" class="btn btn-primary">Add New Product</a>
<table class="table mt-4">
    <thead>
        <tr>
            <th>Name</th>
            <th>VAT Rate</th>
            <th>Expense Code</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for product in products %}
            <tr>
                <td>{{ product.name }}</td>
                <td>{{ product.vat_rate }}</td>
                <td>{{ product.expense_code }}</td>
                <td>
                    <a href="{% url 'product-update' product.pk %}" class="btn btn-warning">Edit</a>
                    <a href="{% url 'product-delete' product.pk %}" class="btn btn-danger">Delete</a>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="4">No products found.</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}

```

# testapp/templates/profile.html

```html
{% extends 'base.html' %}

{% block title %}Profile{% endblock %}

{% block content %}
    <h1>Profile Page</h1>
    <p>First Name: {{ user.first_name }}</p>
    <p>Last Name: {{ user.last_name }}</p>
    <p>Email: {{ user.email }}</p>
{% endblock %}

```

# testapp/templates/supplier/supplier_confirm_delete.html

```html
{% extends 'base.html' %}

{% block title %}Delete Supplier{% endblock %}

{% block content %}
<h1>Delete Supplier</h1>
<p>Are you sure you want to delete "{{ supplier.name }}"?</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirm Deletion</button>
    <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/supplier/supplier_form.html

```html
{% extends 'base.html' %}

{% block title %}Supplier Form{% endblock %}

{% block content %}
<h1>{{ view.object.pk|default:'Add New Supplier' }}</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-success">Save</button>
    <a href="{% url 'supplier-list' %}" class="btn btn-secondary">Cancel</a>
</form>
{% endblock %}

```

# testapp/templates/supplier/supplier_list.html

```html
{% extends 'base.html' %}

{% block title %}Supplier List{% endblock %}

{% block content %}
<h1>Supplier List</h1>
<a href="{% url 'supplier-create' %}" class="btn btn-primary">Add New Supplier</a>
<table class="table mt-4">
    <thead>
        <tr>
            <th>Name</th>
            <th>IF Code</th>
            <th>ICE Code</th>
            <th>RC Code</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for supplier in suppliers %}
            <tr>
                <td>{{ supplier.name }}</td>
                <td>{{ supplier.if_code }}</td>
                <td>{{ supplier.ice_code }}</td>
                <td>{{ supplier.rc_code }}</td>
                <td>
                    <a href="{% url 'supplier-update' supplier.pk %}" class="btn btn-warning">Edit</a>
                    <a href="{% url 'supplier-delete' supplier.pk %}" class="btn btn-danger">Delete</a>
                </td>
            </tr>
        {% empty %}
            <tr>
                <td colspan="5">No suppliers found.</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}

```

# testapp/templatetags/__init__.py

```py

```

# testapp/templatetags/accounting_filters.py

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

# testapp/templatetags/check_tags.py

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

# testapp/tests.py

```py
from django.test import TestCase

# Create your tests here.

```

# testapp/urls.py

```py
from django.urls import path
from . import views
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView
from .views_product import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductAjaxCreateView, ProductDetailsView
from .views_invoice import (
    InvoiceListView, InvoiceCreateView, InvoiceUpdateView, InvoiceDeleteView, InvoiceDetailsView,
    product_autocomplete, AddProductToInvoiceView, EditProductInInvoiceView, ExportInvoicesView, UnexportInvoiceView,
    InvoicePaymentDetailsView, InvoiceAccountingSummaryView  # Import the EditProductInInvoiceView
)
from .views_checkers import (
    CheckerListView, CheckerCreateView, CheckerDetailsView, CheckCreateView, CheckListView, CheckStatusView,
    invoice_autocomplete, supplier_autocomplete, CheckerDeleteView, CheckUpdateView, CheckCancelView
)

from .views_credit_notes import CreditNoteDetailsView, CreateCreditNoteView

urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view

    # Supplier CRUD operations
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),  # List all suppliers
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier-create'),  # Create a new supplier
    path('suppliers/<uuid:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),  # Update a supplier
    path('suppliers/<uuid:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),  # Delete a supplier

    # Product CRUD operations
    path('products/', ProductListView.as_view(), name='product-list'),  # List all products
    path('products/create/', ProductCreateView.as_view(), name='product-create'),  # Create a new product
    path('products/<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),  # Update a product
    path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),  # Delete a product
    path('products/<uuid:pk>/details/', ProductDetailsView.as_view(), name='product-details'),  # Details for a specific product
    path('products/ajax-create/', ProductAjaxCreateView.as_view(), name='product-ajax-create'),  # AJAX view for creating a new Product

    # Invoice CRUD operations
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

    path('suppliers/autocomplete/', supplier_autocomplete, name='supplier-autocomplete'),  # Autocomplete for suppliers
    path('checkers/', CheckerListView.as_view(), name='checker-list'),  # List all checkers
    path('checkers/create/', CheckerCreateView.as_view(), name='checker-create'),
    path('checkers/<uuid:pk>/details/', CheckerDetailsView.as_view(), name='checker-details'),
    path('checkers/<uuid:pk>/delete/', CheckerDeleteView.as_view(), name='checker-delete'),
    path('checks/create/', CheckCreateView.as_view(), name='check-create'),
    path('checks/', CheckListView.as_view(), name='check-list'),
    path('checks/<uuid:pk>/mark-delivered/', 
        CheckStatusView.as_view(), {'action': 'delivered'}, name='check-mark-delivered'),
    path('checks/<uuid:pk>/mark-paid/', 
        CheckStatusView.as_view(), {'action': 'paid'}, name='check-mark-paid'),
    path('invoices/autocomplete/', invoice_autocomplete, name='invoice-autocomplete'),
    path('checks/<uuid:pk>/', CheckUpdateView.as_view(), name='check-update'),
    path('checks/<uuid:pk>/cancel/', CheckCancelView.as_view(), name='check-cancel'),

    path('invoices/<str:invoice_id>/credit-note-details/', CreditNoteDetailsView.as_view(), name='credit-note-details'),

    path('invoices/create-credit-note/', 
         CreateCreditNoteView.as_view(), 
         name='create-credit-note'),

]

```

# testapp/views_checkers.py

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Checker, Check, Invoice, Supplier
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


class CheckerListView(ListView):
    model = Checker
    template_name = 'checker/checker_list.html'
    context_object_name = 'checkers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = Checker.BANK_CHOICES
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CheckerCreateView(View):
        def post(self, request):
            try:
                print("Received data:", request.body)
                data = json.loads(request.body)
                print("Parsed data:", data)
                
                # Validate final page
                starting_page = int(data['starting_page'])
                num_pages = int(data['num_pages'])
                calculated_final = starting_page + num_pages - 1
                
                checker = Checker.objects.create(
                    type=data['type'],
                    bank=data['bank'],
                    account_number=data['account_number'],
                    city=data['city'],
                    num_pages=num_pages,
                    index=data['index'].upper(),
                    starting_page=starting_page,
                    final_page=calculated_final
                )
                
                return JsonResponse({
                    'message': 'Checker created successfully',
                    'checker_id': str(checker.id)
                })
                
            except Exception as e:
                print("Error:", e)
                return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckerDetailsView(View):
        def get(self, request, pk):
            try:
                checker = get_object_or_404(Checker, pk=pk)
                return JsonResponse({
                    'code': checker.code,
                    'type': checker.type,
                    'bank': checker.get_bank_display(),
                    'account_number': checker.account_number,
                    'city': checker.city,
                    'num_pages': checker.num_pages,
                    'index': checker.index,
                    'starting_page': checker.starting_page,
                    'final_page': checker.final_page,
                    'current_position': checker.current_position,
                    'remaining_pages': checker.final_page - checker.current_position + 1
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

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            invoice = get_object_or_404(Invoice, pk=data['invoice_id'])

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            
            check = Check.objects.create(
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
        return Check.objects.select_related('checker', 'beneficiary', 'cause')


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
```

# testapp/views_credit_notes.py

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

# testapp/views_invoice.py

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
from decimal import Decimal
from django.template.loader import render_to_string


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
            queryset = Invoice.objects.all().select_related('supplier')  # Add select_related for performance
            
            # Debug prints
            print("Request GET params:", self.request.GET)

           
                # Date Range Filter
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            if date_from:
                try:
                    queryset = queryset.filter(date__gte=date_from)
                except Exception as e:
                    print(f"Error filtering by date_from: {e}")
            if date_to:
                try:
                    queryset = queryset.filter(date__lte=date_to)
                except Exception as e:
                    print(f"Error filtering by date_to: {e}")

            # Amount Range Filter
            amount_min = self.request.GET.get('amount_min')
            amount_max = self.request.GET.get('amount_max')

            if amount_min or amount_max:
                # First get all invoices
                invoices = list(queryset)  # Convert to list to evaluate the queryset
                filtered_invoices = []

                amount_min = Decimal(amount_min if amount_min else '0')
                amount_max = Decimal(amount_max if amount_max else '999999999')

                # Filter based on net_amount property
                for invoice in invoices:
                    net_amount = invoice.net_amount
                    if amount_min <= net_amount <= amount_max:
                        filtered_invoices.append(invoice.id)

                # Filter queryset by IDs
                queryset = queryset.filter(id__in=filtered_invoices)

                print(f"Debug - Amount range: {amount_min} to {amount_max}")
                print(f"Debug - Filtered invoices count: {len(filtered_invoices)}")
                for inv_id in filtered_invoices:
                    invoice = next(inv for inv in invoices if inv.id == inv_id)
                    print(f"Debug - Invoice {invoice.ref}: Net amount = {invoice.net_amount}")



            # Supplier Filter
            supplier = self.request.GET.get('supplier')
            if supplier:
                print(f"Filtering by supplier: {supplier}")
                queryset = queryset.filter(supplier_id=supplier)

            # Payment Status Filter
            payment_status = self.request.GET.get('payment_status')
            if payment_status:
                queryset = queryset.filter(payment_status=payment_status)

            # Export Status Filter
            export_status = self.request.GET.get('export_status')
            if export_status == 'exported':
                queryset = queryset.filter(exported_at__isnull=False)
            elif export_status == 'not_exported':
                queryset = queryset.filter(exported_at__isnull=True)

            # Product Filter
            product_id = self.request.GET.get('product')
            if product_id:
                queryset = queryset.filter(products__product_id=product_id)

            # Payment Status Filters
            has_pending_checks = self.request.GET.get('has_pending_checks')
            if has_pending_checks:
                queryset = queryset.filter(check__status='pending').distinct()

            has_delivered_unpaid = self.request.GET.get('has_delivered_unpaid')
            if has_delivered_unpaid:
                queryset = queryset.filter(check__status='delivered').exclude(check__status='paid').distinct()

            # Energy Filter
            is_energy = self.request.GET.get('is_energy')
            if is_energy:
                queryset = queryset.filter(supplier__is_energy=True)

            # Credit Note Status
            credit_note_status = self.request.GET.get('credit_note_status')
            if credit_note_status == 'has_credit_notes':
                queryset = queryset.filter(credit_notes__isnull=False).distinct()
            elif credit_note_status == 'no_credit_notes':
                queryset = queryset.filter(credit_notes__isnull=True)
            elif credit_note_status == 'partially_credited':
                # Invoices that have credit notes but are not fully credited
                queryset = queryset.filter(
                    credit_notes__isnull=False,
                    payment_status__in=['not_paid', 'partially_paid']
                ).distinct()

            # Due Date Range
            due_date_from = self.request.GET.get('due_date_from')
            due_date_to = self.request.GET.get('due_date_to')
            if due_date_from:
                queryset = queryset.filter(payment_due_date__gte=due_date_from)
            if due_date_to:
                queryset = queryset.filter(payment_due_date__lte=due_date_to)

            # Overdue Filter
            is_overdue = self.request.GET.get('is_overdue')
            if is_overdue:
                today = timezone.now().date()
                queryset = queryset.filter(
                    payment_due_date__lt=today,
                    payment_status__in=['not_paid', 'partially_paid']
                )

            # Print final queryset SQL
            print("Final query SQL:", queryset.query)

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
            'reference': f"{check.checker.bank}-{check.position}",
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

# testapp/views_product.py

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

# testapp/views_supplier.py

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

# testapp/views.py

```py
from django.shortcuts import render
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

