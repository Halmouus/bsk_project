# Generated by Django 4.2.16 on 2024-11-27 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='check',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
