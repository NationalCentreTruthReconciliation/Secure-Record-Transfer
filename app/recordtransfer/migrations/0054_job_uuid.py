# Generated by Django 4.2.20 on 2025-07-15 18:48

import uuid

from django.db import migrations, models


def generate_unique_uuids(apps, schema_editor):
    Job = apps.get_model("recordtransfer", "Job")
    for job in Job.objects.all():
        job.uuid = uuid.uuid4()
        job.save()


class Migration(migrations.Migration):
    dependencies = [
        ("recordtransfer", "0053_remove_submission_bag_name"),
    ]

    operations = [
        # First add the field without unique constraint
        migrations.AddField(
            model_name="job",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4),
        ),
        # Generate unique UUIDs for existing records
        migrations.RunPython(generate_unique_uuids),
        # Then add the unique constraint
        migrations.AlterField(
            model_name="job",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
