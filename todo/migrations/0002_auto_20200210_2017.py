# Generated by Django 3.0.3 on 2020-02-11 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='todoitem',
            old_name='time',
            new_name='duedate',
        ),
        migrations.RemoveField(
            model_name='todoitem',
            name='date',
        ),
        migrations.AddField(
            model_name='todoitem',
            name='description',
            field=models.CharField(default='', max_length=600),
        ),
    ]