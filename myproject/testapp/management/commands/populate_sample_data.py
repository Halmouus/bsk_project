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