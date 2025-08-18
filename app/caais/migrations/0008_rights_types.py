from django.db import migrations

from caais.models import RightsType


def populate_rights_types(apps, schema_editor):
    """Add a few rights type terms to database"""

    rights_types_data = [
        ("Other", "A type of rights not listed elsewhere"),
        ("Unknown", "Use when it is not known what type of rights pertain to the material"),
        ("Cultural Rights", "Accss to material is limited according to cultural protocols"),
        ("Statute", "Access to material is limited according to law or legislation"),
        ("License", "Access to material is limited by a licensing agreement"),
        ("Access", "Access to material is restricted to a certain entity or group of entities"),
        (
            "Copyright",
            "Access to material is based on fair dealing OR material is in the public domain",
        ),
    ]

    for name, description in rights_types_data:
        rights_type = RightsType.objects.filter(name=name).first()
        if not rights_type:
            RightsType.objects.create(
                name=name,
                description=description,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("caais", "0007_rights_rightstype_storagelocation"),
    ]

    operations = [
        migrations.RunPython(populate_rights_types),
    ]
