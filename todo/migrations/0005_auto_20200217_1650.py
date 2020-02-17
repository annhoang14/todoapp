# Generated by Django 3.0.3 on 2020-02-17 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0004_todoitem_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='todoitem',
            name='end_recur_date',
            field=models.DateTimeField(default='2020-02-17 05:00'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='todoitem',
            name='recur_freq',
            field=models.TextField(default='Never', max_length=7),
            preserve_default=False,
        ),
    ]
