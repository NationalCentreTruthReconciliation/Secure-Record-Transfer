from django.db import migrations

from caais.models import ExtentType


def populate_extents(apps, schema_editor):
    """Add a few extent type terms to database"""

    extent_types_data = [
        ("Extent received", "Extent of material as it was received"),
        ("Extent retained", "Extent of retained material"),
        ("Extent removed", "Extent of removed material"),
    ]

    for name, description in extent_types_data:
        extent_type = ExtentType.objects.filter(name=name).first()
        if not extent_type:
            ExtentType.objects.create(
                name=name,
                description=description,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("caais", "0005_auto_20220414_1326"),
    ]

    operations = [
        migrations.RunPython(populate_extents),
    ]
