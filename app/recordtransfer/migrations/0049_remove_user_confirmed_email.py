# Generated by Django 4.2.20 on 2025-06-02 15:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0048_alter_inprogresssubmission_current_step'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='confirmed_email',
        ),
    ]
