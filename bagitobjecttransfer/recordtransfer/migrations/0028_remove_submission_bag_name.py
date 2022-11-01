# Generated by Django 3.2.11 on 2022-10-24 20:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0027_auto_20220704_1020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='bag_name',
        ),
        migrations.AlterField(
            model_name='appraisal',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appraisals',
                                    to='recordtransfer.submission'),
        ),
    ]