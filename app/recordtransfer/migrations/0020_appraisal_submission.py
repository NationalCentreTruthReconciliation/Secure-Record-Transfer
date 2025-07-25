# Generated by Django 3.2.11 on 2022-01-12 19:26

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0019_auto_20220111_0931'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bag',
            name='review_status',
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_date', models.DateTimeField()),
                ('review_status', models.CharField(choices=[('NR', 'Not Reviewed'), ('RS', 'Review Started'), ('RC', 'Review Complete')], default='NR', max_length=2)),
                ('accession_identifier', models.CharField(default='', max_length=128, null=True)),
                ('level_of_detail', models.CharField(choices=[('NS', 'Not Specified'), ('ML', 'Minimal'), ('PL', 'Partial'), ('FL', 'Full')], default='NS', max_length=2)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('bag', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='recordtransfer.bag')),
            ],
        ),
        migrations.CreateModel(
            name='Appraisal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appraisal_type', models.CharField(choices=[('AP', 'Archival Appraisal'), ('MP', 'Monetary Appraisal')], max_length=2)),
                ('appraisal_date', models.DateTimeField()),
                ('statement', models.TextField()),
                ('note', models.TextField(default='', null=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recordtransfer.submission')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
