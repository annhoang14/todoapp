# Generated by Django 3.0.3 on 2020-03-21 22:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0051_auto_20200321_1753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extracurricular',
            name='end_date',
            field=models.DateField(blank=True, default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='extracurricular',
            name='start_date',
            field=models.DateField(blank=True, default=datetime.date.today),
        ),
    ]
