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