# Generated by Django 4.2.18 on 2025-01-22 21:32

from django.db import migrations, models
import django.db.models.deletion
import recordtransfer.models
import recordtransfer.storage


class Migration(migrations.Migration):

    replaces = [('recordtransfer', '0043_storeduploadedfile_tempuploadedfile_and_more'), ('recordtransfer', '0044_uploadsession_expired'), ('recordtransfer', '0045_rename_storeduploadedfile_permuploadedfile'), ('recordtransfer', '0046_alter_permuploadedfile_options_and_more'), ('recordtransfer', '0047_remove_uploadsession_expired_uploadsession_status'), ('recordtransfer', '0048_alter_uploadsession_status'), ('recordtransfer', '0049_alter_uploadsession_status')]

    dependencies = [
        ('recordtransfer', '0042_alter_uploadedfile_session'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermUploadedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='-', max_length=256, null=True)),
                ('file_upload', models.FileField(null=True, storage=recordtransfer.storage.UploadedFileStorage, upload_to='')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.uploadsession')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Permanent uploaded file',
                'verbose_name_plural': 'Permanent uploaded files',
            },
        ),
        migrations.CreateModel(
            name='TempUploadedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='-', max_length=256, null=True)),
                ('file_upload', models.FileField(null=True, storage=recordtransfer.storage.TempFileStorage, upload_to=recordtransfer.models.session_upload_location)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.uploadsession')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Temporary uploaded file',
                'verbose_name_plural': 'Temporary uploaded files',
            },
        ),
        migrations.DeleteModel(
            name='UploadedFile',
        ),
        migrations.AddField(
            model_name='uploadsession',
            name='status',
            field=models.CharField(choices=[('CR', 'Session Created'), ('EX', 'Session Expired'), ('UG', 'Uploading Files'), ('CP', 'File Copy in Progress'), ('SD', 'All Files in Permanent Storage'), ('FD', 'Copying Failed'), ('RP', 'File Removal in Progress'), ('DL', 'All Files Removed')], default='CR', max_length=2),
        ),
    ]
