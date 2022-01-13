# Generated by Django 3.1.1 on 2020-09-15 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0002_auto_20200915_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_allowed_to_transfer',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_archivist',
        ),
        migrations.AddField(
            model_name='user',
            name='gets_bag_email_updates',
            field=models.BooleanField(default=False),
        ),
    ]