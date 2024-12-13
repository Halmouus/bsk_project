# Generated by Django 4.2.16 on 2024-12-12 22:28

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0003_accountingentry_bankstatement'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterBankTransfer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('label', models.CharField(default='Interbank Transfer', max_length=255)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('is_deleted', models.BooleanField(default=False)),
                ('from_bank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='outgoing_transfers', to='testapp.bankaccount')),
                ('to_bank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incoming_transfers', to='testapp.bankaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferredRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_type', models.CharField(max_length=50)),
                ('source_id', models.UUIDField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('original_date', models.DateField()),
                ('original_label', models.CharField(max_length=255)),
                ('original_reference', models.CharField(max_length=100)),
                ('transfer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferred_records', to='testapp.interbanktransfer')),
            ],
            options={
                'unique_together': {('source_type', 'source_id')},
            },
        ),
    ]