# Generated by Django 4.2.16 on 2024-12-10 20:34

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='invoice',
            name='unique_supplier_invoice_ref',
        ),
        migrations.RemoveConstraint(
            model_name='product',
            name='unique_product_name_expense_code',
        ),
        migrations.RemoveConstraint(
            model_name='supplier',
            name='unique_supplier_name_rc_code',
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='bank_overdraft',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum allowed overdraft amount', max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='check_discount_line_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum amount available for check discounting', max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='has_check_discount_line',
            field=models.BooleanField(default=False, help_text='Indicates if this account can discount checks'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='has_lcn_discount_line',
            field=models.BooleanField(default=False, help_text='Indicates if this account can discount LCNs'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='is_current',
            field=models.BooleanField(default=False, help_text='Determines if accounting operations are recorded on this account'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='lcn_discount_line_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum amount available for LCN discounting', max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='overdraft_fee',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Fee applied for overdraft usage', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='stamp_fee_per_receipt',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Stamp fee charged per presented receipt', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='cashreceipt',
            name='compensating_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_compensating', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='cashreceipt',
            name='compensating_object_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='clientsale',
            name='sale_type',
            field=models.CharField(choices=[('BRICKS', 'Bricks'), ('TRANSPORT', 'Transport')], default='BRICKS', max_length=10),
        ),
        migrations.AddField(
            model_name='presentationreceipt',
            name='immutable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='presentationreceipt',
            name='recorded_status',
            field=models.CharField(blank=True, choices=[('PORTFOLIO', 'In Portfolio'), ('PRESENTED_COLLECTION', 'Presented for Collection'), ('PRESENTED_DISCOUNT', 'Presented for Discount'), ('DISCOUNTED', 'Discounted'), ('PAID', 'Paid'), ('REJECTED', 'Rejected'), ('COMPENSATED', 'Compensated'), ('UNPAID', 'Unpaid')], help_text='Stores the final status decision made in this presentation', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='transferreceipt',
            name='compensating_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_compensating', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='transferreceipt',
            name='compensating_object_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='clientsale',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='clientsale',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testapp.client'),
        ),
    ]