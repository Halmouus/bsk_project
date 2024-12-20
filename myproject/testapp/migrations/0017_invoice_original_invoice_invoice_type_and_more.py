# Generated by Django 4.2.16 on 2024-11-24 23:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0016_invoice_payment_status_alter_checker_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='original_invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='credit_notes', to='testapp.invoice'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='type',
            field=models.CharField(choices=[('invoice', 'Invoice'), ('credit_note', 'Credit Note')], default='invoice', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('original_invoice__isnull', True), ('type', 'invoice')), models.Q(('original_invoice__isnull', False), ('type', 'credit_note')), _connector='OR')), name='credit_note_must_have_original_invoice'),
        ),
    ]
