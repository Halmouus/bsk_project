from django.core.management.base import BaseCommand
from testapp.models import Product, Supplier
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Generate random products and suppliers for testing'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=10, help='Number of products to create')
        parser.add_argument('--suppliers', type=int, default=5, help='Number of suppliers to create')

    def handle(self, *args, **options):
        # Product data
        product_types = [
            'Electricity', 'Gas', 'Water', 'Internet', 'Phone', 
            'Office Supplies', 'Cleaning', 'Maintenance', 'Software', 
            'Hardware', 'Consulting', 'Training', 'Marketing', 'Insurance'
        ]
        
        vat_rates = [0, 7, 10, 14, 20]
        expense_codes = ['61111', '61112', '61113', '61114', '61115', '61116', '61117']

        # Create Products
        for i in range(options['products']):
            name = f"{random.choice(product_types)} {random.randint(1000, 9999)}"
            try:
                Product.objects.create(
                    name=name,
                    vat_rate=Decimal(str(random.choice(vat_rates))),
                    expense_code=random.choice(expense_codes),
                    is_energy=random.choice([True, False]),
                    fiscal_label=f"FISC-{random.randint(1000, 9999)}"
                )
                self.stdout.write(self.style.SUCCESS(f'Created product: {name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create product {name}: {str(e)}'))

        # Supplier data
        cities = ['Casablanca', 'Rabat', 'Marrakech', 'Fes', 'Tanger', 'Agadir']
        services = ['Energy', 'Telecom', 'IT', 'Consulting', 'Maintenance']

        # Create Suppliers
        for i in range(options['suppliers']):
            name = f"Supplier-{random.randint(1000, 9999)}"
            try:
                Supplier.objects.create(
                    name=name,
                    if_code=f"IF{random.randint(100000, 999999)}",
                    ice_code=f"{random.randint(1000000000000, 9999999999999)}",
                    rc_code=f"{random.randint(10000, 999999)}",
                    rc_center=random.choice(cities),
                    accounting_code=f"401{random.randint(1000, 9999)}",
                    is_energy=random.choice([True, False]),
                    service=random.choice(services),
                    delay_convention=random.randint(30, 90),
                    is_regulated=random.choice([True, False])
                )
                self.stdout.write(self.style.SUCCESS(f'Created supplier: {name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create supplier {name}: {str(e)}')) 