from django.db import migrations

from caais.models import ExtentType


def populate_extents(apps, schema_editor):
    ''' Add a few extent type terms to database '''

    for name, description in (
            ('Extent received', 'Extent of material as it was received'),
            ('Extent retained', 'Extent of retained material'),
            ('Extent removed', 'Extent of removed material'),
        ):
        extent_type, _ = ExtentType.objects.get_or_create(
            name=name,
            description=description,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('caais', '0005_auto_20220414_1326'),
    ]

    operations = [
        migrations.RunPython(populate_extents),
    ]
