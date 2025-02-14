from django.core.management.base import BaseCommand
from django.utils import timezone
from testapp.models import CheckReceipt, LCN, Client, Entity, BankAccount
import random
from decimal import Decimal
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates test negotiable receipts (checks and LCNs)'

    def handle(self, *args, **kwargs):
        print("\n=== Creating Test Receipts ===")
        
        # Get or create test client and entity
        client, created = Client.objects.get_or_create(
            name="Test Client",
            defaults={
                'client_code': '34200'
            }
        )
        print(f"Client {'created' if created else 'found'}: {client.name}")
        
        entity, created = Entity.objects.get_or_create(
            name="Test Entity",
            defaults={
                'ice_code': '123456789012345',
                'accounting_code': '34200'
            }
        )
        print(f"Entity {'created' if created else 'found'}: {entity.name}")
        
        # Get first bank account
        bank_account = BankAccount.objects.first()
        if not bank_account:
            self.stdout.write("Please create at least one bank account first")
            return
        print(f"Using bank account: {bank_account}")

        # Create checks using model's methods
        for i in range(30):
            check = CheckReceipt(
                client=client,
                entity=entity,
                check_number=f"TEST{i+1:06d}",
                amount=Decimal(random.randint(1000, 20000)),
                due_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                issuing_bank='ATW',
                bank_account=bank_account,
                status='PORTFOLIO',
                operation_date=timezone.now().date()
            )
            check.save()
            self.stdout.write(f"Created check: {check.check_number}")

        # Create LCNs using model's methods
        for i in range(20):
            lcn = LCN(
                client=client,
                entity=entity,
                lcn_number=f"LCN{i+1:06d}",
                amount=Decimal(random.randint(1000, 50000)),
                due_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                issuing_bank='ATW',
                bank_account=bank_account,
                status='PORTFOLIO',
                operation_date=timezone.now().date()
            )
            lcn.save()
            self.stdout.write(f"Created LCN: {lcn.lcn_number}")
