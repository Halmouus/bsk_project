from django.core.management.base import BaseCommand
from django.db import transaction
from testapp.models import Product, Supplier, Invoice
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generate test data for financial system'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=10)
        parser.add_argument('--suppliers', type=int, default=5)
        parser.add_argument('--invoices', type=int, default=10)

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Creating products...')
        products = []
        for i in range(options['products']):
            product = Product.objects.create(
                name=f"Product-{i+1}",
                vat_rate=Decimal('20.00'),
                expense_code=f'611{i+1:02d}',
                is_energy=i < 3,
                fiscal_label=f"FISC-{i+1:04d}"
            )
            products.append(product)
            self.stdout.write(f'Created product {i+1}')

        self.stdout.write('Creating suppliers...')
        suppliers = []
        cities = ['Casablanca', 'Rabat', 'Marrakech', 'Tanger', 'Agadir']
        for i in range(options['suppliers']):
            supplier = Supplier.objects.create(
                name=f"Supplier-{i+1}",
                if_code=f"IF{random.randint(100000, 999999)}",
                ice_code=f"{random.randint(1000000000000, 9999999999999)}",
                rc_code=f"{i+1:05d}",
                rc_center=random.choice(cities),
                accounting_code=f"401{i+1:04d}",
                is_energy=i < 2,
                service=random.choice(['Energy', 'Telecom', 'IT', 'Maintenance']),
                delay_convention=random.choice([30, 45, 60])
            )
            suppliers.append(supplier)
            self.stdout.write(f'Created supplier {i+1}')

        self.stdout.write('Creating invoices...')
        for i in range(options['invoices']):
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 60))
            supplier = random.choice(suppliers)
            invoice = Invoice.objects.create(
                supplier=supplier,
                invoice_number=f"INV-{i+1:05d}",
                invoice_date=invoice_date,
                due_date=invoice_date + timedelta(days=supplier.delay_convention),
                amount=Decimal(random.uniform(1000, 50000)).quantize(Decimal('0.01')),
                vat_amount=Decimal(random.uniform(200, 10000)).quantize(Decimal('0.01')),
                status='pending',
                is_validated=False
            )
            # Add 1-3 random products
            invoice.products.add(*random.sample(products, k=random.randint(1, 3)))
            self.stdout.write(f'Created invoice {i+1}')

        self.stdout.write(self.style.SUCCESS('Done!'))