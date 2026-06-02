"""Add an opaque ``uuid`` field to TempUploadedFile and PermUploadedFile.

The UUID is used in user-facing file access URLs so the underlying
``UploadSession.token`` no longer needs to be embedded in those URLs.

Because the field is ``unique=True`` with a callable default, the migration is
applied in three steps per model:

1. Add the column as nullable (no unique constraint, no default).
2. Populate UUIDs for every existing row.
3. Apply the default + unique + not-null constraints.
"""

import uuid

from django.db import migrations, models


def populate_uuids(apps, schema_editor) -> None:  # noqa: ANN001
    """Assign a fresh UUID to every existing TempUploadedFile and PermUploadedFile."""
    for model_name in ("TempUploadedFile", "PermUploadedFile"):
        Model = apps.get_model("upload", model_name)
        for instance in Model.objects.all():
            instance.uuid = uuid.uuid4()
            instance.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    """Add the uuid field to uploaded-file models for token-less access URLs."""

    dependencies = [
        ("upload", "0002_add_archivist_permissions"),
    ]

    operations = [
        # Step 1: add the column as nullable so existing rows are not rejected.
        migrations.AddField(
            model_name="tempuploadedfile",
            name="uuid",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name="permuploadedfile",
            name="uuid",
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: populate UUIDs for every existing row.
        migrations.RunPython(populate_uuids, reverse_code=migrations.RunPython.noop),
        # Step 3: apply the default + unique + not-null constraints.
        migrations.AlterField(
            model_name="tempuploadedfile",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="permuploadedfile",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
