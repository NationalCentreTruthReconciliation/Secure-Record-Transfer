# Generated by Django 4.2.19 on 2025-03-05 17:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('recordtransfer', '0046_alter_uploadsession_status'), ('recordtransfer', '0047_alter_inprogresssubmission_upload_session')]

    dependencies = [
        ('recordtransfer', '0045_uploadsession_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadsession',
            name='status',
            field=models.CharField(choices=[('CR', 'Session Created'), ('EX', 'Session Expired'), ('UG', 'Uploading Files'), ('CP', 'File Copy in Progress'), ('SD', 'All Files in Permanent Storage'), ('FD', 'Copying Failed'), ('RP', 'File Removal in Progress')], default='CR', max_length=2),
        ),
        migrations.AlterField(
            model_name='inprogresssubmission',
            name='upload_session',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='in_progress_submission', to='recordtransfer.uploadsession'),
        ),
    ]
