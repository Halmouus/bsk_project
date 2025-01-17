from django.core.management.base import BaseCommand
from testapp.models import UserRole
from django.db import transaction

class Command(BaseCommand):
    help = 'Create default user roles'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating user roles...')
        
        try:
            with transaction.atomic():
                # Create Admin Role
                admin_role, created = UserRole.objects.get_or_create(
                    name='Admin',
                    defaults={
                        'description': 'Full system access including user management',
                        'can_manage_users': True,
                        'can_view_bank': True,
                        'can_manage_bank': True,
                        'can_view_checks': True,
                        'can_manage_checks': True,
                        'can_view_clients': True,
                        'can_manage_clients': True,
                        'can_view_suppliers': True,
                        'can_manage_suppliers': True,
                        'can_view_products': True,
                        'can_manage_products': True,
                        'can_view_invoices': True,
                        'can_manage_invoices': True,
                        'can_view_receipts': True,
                        'can_manage_receipts': True,
                        'can_view_contracts': True,
                        'can_manage_contracts': True,
                        'can_view_bank_accounts': True,
                        'can_manage_bank_accounts': True,
                    }
                )
                self.stdout.write(f'{"Created" if created else "Updated"} Admin role')

                # Create Supervisor Role
                supervisor_role, created = UserRole.objects.get_or_create(
                    name='Supervisor',
                    defaults={
                        'description': 'Can view everything but cannot modify',
                        'can_view_bank': True,
                        'can_view_checks': True,
                        'can_view_clients': True,
                        'can_view_suppliers': True,
                        'can_view_products': True,
                        'can_view_invoices': True,
                        'can_view_receipts': True,
                        'can_view_contracts': True,
                        'can_view_bank_accounts': True,
                    }
                )
                self.stdout.write(f'{"Created" if created else "Updated"} Supervisor role')

                # Create Client Keeper Role
                client_keeper_role, created = UserRole.objects.get_or_create(
                    name='Client Keeper',
                    defaults={
                        'description': 'Manages clients and receipts',
                        'can_view_bank': True,
                        'can_view_checks': True,
                        'can_view_clients': True,
                        'can_manage_clients': True,
                        'can_view_suppliers': True,
                        'can_view_products': True,
                        'can_view_invoices': True,
                        'can_view_receipts': True,
                        'can_manage_receipts': True,
                        'can_view_contracts': True,
                        'can_view_bank_accounts': True,
                    }
                )
                self.stdout.write(f'{"Created" if created else "Updated"} Client Keeper role')

                # Create Supplier Keeper Role
                supplier_keeper_role, created = UserRole.objects.get_or_create(
                    name='Supplier Keeper',
                    defaults={
                        'description': 'Manages suppliers, products, invoices and contracts',
                        'can_view_bank': True,
                        'can_view_checks': True,
                        'can_view_clients': True,
                        'can_view_suppliers': True,
                        'can_manage_suppliers': True,
                        'can_view_products': True,
                        'can_manage_products': True,
                        'can_view_invoices': True,
                        'can_manage_invoices': True,
                        'can_view_receipts': True,
                        'can_view_contracts': True,
                        'can_manage_contracts': True,
                        'can_view_bank_accounts': True,
                    }
                )
                self.stdout.write(f'{"Created" if created else "Updated"} Supplier Keeper role')

                # Create Bank Keeper Role
                bank_keeper_role, created = UserRole.objects.get_or_create(
                    name='Bank Keeper',
                    defaults={
                        'description': 'Manages bank accounts, checks and related operations',
                        'can_view_bank': True,
                        'can_manage_bank': True,
                        'can_view_checks': True,
                        'can_manage_checks': True,
                        'can_view_clients': True,
                        'can_view_suppliers': True,
                        'can_view_products': True,
                        'can_view_invoices': True,
                        'can_view_receipts': True,
                        'can_view_contracts': True,
                        'can_view_bank_accounts': True,
                        'can_manage_bank_accounts': True,
                    }
                )
                self.stdout.write(f'{"Created" if created else "Updated"} Bank Keeper role')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating roles: {str(e)}'))
            raise

        self.stdout.write(self.style.SUCCESS('Successfully created all user roles')) 