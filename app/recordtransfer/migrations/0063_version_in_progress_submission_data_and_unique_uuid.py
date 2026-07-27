import uuid
from typing import Any, ClassVar

from django.db import migrations, models
from django.db.models import Count


def version_legacy_wizard_data(apps: Any, schema_editor: Any) -> None:
    """Mark existing save-for-later wizard data as the legacy version."""
    InProgressSubmission = apps.get_model("recordtransfer", "InProgressSubmission")
    for submission in InProgressSubmission.objects.iterator():
        step_data = submission.step_data
        if isinstance(step_data, dict) and "past" in step_data and "version" not in step_data:
            submission.step_data = {"version": 1, **step_data}
            submission.save(update_fields=["step_data"])


def unversion_legacy_wizard_data(apps: Any, schema_editor: Any) -> None:
    """Remove the legacy version marker when reversing this migration."""
    InProgressSubmission = apps.get_model("recordtransfer", "InProgressSubmission")
    for submission in InProgressSubmission.objects.iterator():
        step_data = submission.step_data
        if isinstance(step_data, dict) and step_data.get("version") == 1:
            submission.step_data = {key: value for key, value in step_data.items() if key != "version"}
            submission.save(update_fields=["step_data"])


def repair_duplicate_uuids(apps: Any, schema_editor: Any) -> None:
    """Assign fresh UUIDs to all but the first row in each duplicate group."""
    InProgressSubmission = apps.get_model("recordtransfer", "InProgressSubmission")
    duplicate_uuids = (
        InProgressSubmission.objects.values("uuid")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for duplicate in duplicate_uuids.iterator():
        rows = InProgressSubmission.objects.filter(uuid=duplicate["uuid"]).order_by("id")
        for submission in rows[1:]:
            new_uuid = uuid.uuid4()
            while InProgressSubmission.objects.filter(uuid=new_uuid).exists():
                new_uuid = uuid.uuid4()
            submission.uuid = new_uuid
            submission.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    """Version legacy wizard data and make submission UUIDs unambiguous."""

    dependencies: ClassVar = [
        ("recordtransfer", "0062_alter_submission_raw_form"),
    ]

    operations: ClassVar = [
        migrations.RunPython(
            version_legacy_wizard_data,
            reverse_code=unversion_legacy_wizard_data,
        ),
        migrations.RunPython(repair_duplicate_uuids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="inprogresssubmission",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
