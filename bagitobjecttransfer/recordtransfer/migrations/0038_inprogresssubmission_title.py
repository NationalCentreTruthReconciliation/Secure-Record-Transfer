# Generated by Django 4.2.16 on 2024-11-13 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0037_merge_20241108_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='inprogresssubmission',
            name='title',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
