# Generated by Django 4.2.16 on 2024-11-07 23:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0004_alter_profile_date_of_joining'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ref', models.CharField(max_length=50, unique=True)),
                ('date', models.DateField()),
                ('fiscal_label', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=4)),
                ('expense_code', models.CharField(max_length=20)),
                ('is_energy', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('if_code', models.CharField(max_length=20, unique=True)),
                ('ice_code', models.CharField(max_length=15, unique=True)),
                ('rc_code', models.CharField(max_length=20)),
                ('rc_center', models.CharField(max_length=100)),
                ('accounting_code', models.CharField(max_length=20, unique=True)),
                ('is_energy', models.BooleanField(default=False)),
                ('service', models.CharField(max_length=255)),
                ('delay_convention', models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)),
                ('is_regulated', models.BooleanField(default=False)),
                ('regulation_file_path', models.FileField(blank=True, null=True, upload_to='supplier_regulations/')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvoiceProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reduction_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=4)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='testapp.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testapp.product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='invoice',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testapp.supplier'),
        ),
    ]
