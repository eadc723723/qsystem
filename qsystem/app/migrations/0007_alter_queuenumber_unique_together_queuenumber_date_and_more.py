# Generated by Django 5.1 on 2024-08-13 08:02

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_queuenumber_counter'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='queuenumber',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='queuenumber',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterUniqueTogether(
            name='queuenumber',
            unique_together={('activity', 'number', 'date')},
        ),
    ]
