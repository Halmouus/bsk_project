# Generated by Django 4.2.16 on 2024-11-08 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0006_alter_invoiceproduct_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft', max_length=20),
        ),
        migrations.AlterField(
            model_name='invoiceproduct',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=20.0, max_digits=5),
        ),
    ]
