from django.core.management.base import BaseCommand
from django.utils import timezone
from testapp.models import CheckReceipt, LCN, Client, Entity, BankAccount
import random
from decimal import Decimal
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates test negotiable receipts (checks and LCNs)'

    def handle(self, *args, **kwargs):
        # Get or create test client and entity
        client, _ = Client.objects.get_or_create(
            name="Test Client",
            defaults={
                'client_code': '34200'
            }
        )
        entity, _ = Entity.objects.get_or_create(
            name="Test Entity",
            defaults={
                'ice_code': '123456789012345',  # 15 digits
                'accounting_code': '34200'  # Must start with '34'
            }
        )
        
        # Get first bank account or create one
        bank_account = BankAccount.objects.first()
        if not bank_account:
            self.stdout.write("Please create at least one bank account first")
            return

        # Create 10 checks
        for i in range(10):
            check = CheckReceipt.objects.create(
                client=client,
                entity=entity,
                check_number=f"TEST{i+1:06d}",
                amount=Decimal(random.randint(1000, 10000)),
                due_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                issuing_bank='ATW',
                bank_account=bank_account,
                status='PORTFOLIO'
            )
            self.stdout.write(f"Created check: {check.check_number}")

        # Create 10 LCNs
        for i in range(10):
            lcn = LCN.objects.create(
                client=client,
                entity=entity,
                lcn_number=f"LCN{i+1:06d}",
                amount=Decimal(random.randint(1000, 10000)),
                due_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                issuing_bank='ATW',
                bank_account=bank_account,
                status='PORTFOLIO'
            )
            self.stdout.write(f"Created LCN: {lcn.lcn_number}")
