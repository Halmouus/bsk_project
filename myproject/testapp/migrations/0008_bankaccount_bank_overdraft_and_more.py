# Generated by Django 4.2.16 on 2024-12-08 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0007_remove_presentationreceipt_rejection_cause_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='bank_overdraft',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Optional amount for overdraft alerts', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='check_discount_line_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum amount for check discounts', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='has_check_discount_line',
            field=models.BooleanField(default=False, help_text='Enable check discount functionality'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='has_lcn_discount_line',
            field=models.BooleanField(default=False, help_text='Enable LCN discount functionality'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='is_current',
            field=models.BooleanField(default=False, help_text='Determines if account is used for active accounting operations'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='lcn_discount_line_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum amount for LCN discounts', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='overdraft_fee',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Fee applied for overdraft', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='stamp_fee_per_receipt',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Fee applied per receipt stamp', max_digits=10, null=True),
        ),
    ]