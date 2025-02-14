from django.core.management.base import BaseCommand
from django.utils import timezone
from testapp.models import BankFeeType, INITIAL_FEE_TYPES

class Command(BaseCommand):
    help = 'Creates initial bank fee types'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n=== Creating Bank Fee Types ==="))
        
        for fee_type in INITIAL_FEE_TYPES:
            bank_fee_type, created = BankFeeType.objects.get_or_create(
                code=fee_type['code'],
                defaults={
                    'name': fee_type['name'],
                    'accounting_code': fee_type['accounting_code'],
                    'vat_code': fee_type['vat_code'],
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {bank_fee_type.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {bank_fee_type.name}")) 