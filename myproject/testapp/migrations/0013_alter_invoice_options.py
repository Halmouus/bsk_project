# Generated by Django 4.2.16 on 2024-11-22 18:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0012_alter_invoice_supplier_alter_invoiceproduct_product'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'permissions': [('can_export_invoice', 'Can export invoice'), ('can_unexport_invoice', 'Can unexport invoice')]},
        ),
    ]
