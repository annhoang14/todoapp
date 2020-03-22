# Generated by Django 3.0.3 on 2020-03-22 02:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0054_todoitem_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todoitem',
            name='progress',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Progress'),
        ),
    ]
