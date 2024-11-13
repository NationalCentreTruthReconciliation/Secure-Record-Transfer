# Generated by Django 4.2.16 on 2024-11-06 18:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0034_auto_20240122_1358'),
    ]

    operations = [
        migrations.CreateModel(
            name='InProgressSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('last_updated', models.DateTimeField(auto_now_add=True)),
                ('current_step', models.CharField(max_length=20)),
                ('step_data', models.BinaryField(default=b'')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='SavedTransfer',
        ),
    ]