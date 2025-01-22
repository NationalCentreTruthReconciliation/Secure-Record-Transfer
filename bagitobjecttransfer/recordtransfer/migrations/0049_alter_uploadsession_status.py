# Generated by Django 4.2.18 on 2025-01-21 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0048_alter_uploadsession_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadsession',
            name='status',
            field=models.CharField(choices=[('CR', 'Session Created'), ('EX', 'Session Expired'), ('UG', 'Uploading Files'), ('CP', 'File Copy in Progress'), ('SD', 'All Files in Permanent Storage'), ('FD', 'Copying Failed'), ('RP', 'File Removal in Progress'), ('DL', 'All Files Removed')], default='CR', max_length=2),
        ),
    ]