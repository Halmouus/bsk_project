# Generated by Django 4.2.16 on 2024-11-22 22:41

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0013_alter_invoice_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Checker',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(blank=True, max_length=10, unique=True)),
                ('type', models.CharField(choices=[('CHQ', 'Cheque'), ('LCN', 'LCN')], max_length=3)),
                ('bank', models.CharField(choices=[('ATW', 'Attijariwafa Bank'), ('BCP', 'Banque Populaire'), ('BOA', 'Bank of Africa'), ('CAM', 'Crédit Agricole du Maroc'), ('CIH', 'CIH Bank'), ('BMCI', 'BMCI'), ('SGM', 'Société Générale Maroc'), ('CDM', 'Crédit du Maroc'), ('ABB', 'Al Barid Bank'), ('CFG', 'CFG Bank'), ('ABM', 'Arab Bank Maroc'), ('CTB', 'Citibank Maghreb')], max_length=4)),
                ('account_number', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator('^\\d+$', 'Only numeric characters allowed.')])),
                ('city', models.CharField(max_length=50, validators=[django.core.validators.RegexValidator('^[A-Za-z\\s]+$', 'Only alphabetical characters allowed.')])),
                ('owner', models.CharField(default='Briqueterie Sidi Kacem', max_length=100)),
                ('num_pages', models.IntegerField(choices=[(25, '25'), (50, '50'), (100, '100')])),
                ('index', models.CharField(max_length=3, validators=[django.core.validators.RegexValidator('^[A-Z]{3}$', 'Must be 3 uppercase letters.')])),
                ('starting_page', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('final_page', models.IntegerField(blank=True)),
                ('current_position', models.IntegerField(blank=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('position', models.CharField(max_length=10)),
                ('creation_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_due', models.DateField(blank=True, null=True)),
                ('amount_due', models.DecimalField(decimal_places=2, editable=False, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('observation', models.TextField(blank=True)),
                ('delivered', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('beneficiary', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.supplier')),
                ('cause', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='testapp.invoice')),
                ('checker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checks', to='testapp.checker')),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='check',
            constraint=models.CheckConstraint(check=models.Q(('amount__lte', models.F('amount_due'))), name='check_amount_cannot_exceed_due'),
        ),
    ]
