# Generated by Django 3.2.25 on 2024-10-23 14:37

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0034_auto_20240122_1358'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissiongroup',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]