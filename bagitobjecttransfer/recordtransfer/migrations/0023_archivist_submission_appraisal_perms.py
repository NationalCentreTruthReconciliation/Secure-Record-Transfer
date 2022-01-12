from django.db import migrations
from django.contrib.auth.models import Group, Permission


def populate_permissions(apps, schema_editor):
    ''' Add permissions to edit rights to archivist staff '''
    group = Group.objects.get(name='archivist_user')
    existing_permissions = group.permissions.all()

    for codename in (
        # Appraisal
        'add_appraisal',
        'change_appraisal',
        'view_appraisal',
        # Submission
        'change_submission',
        'view_submission',
        ):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0022_auto_20220110_1027'),
    ]

    operations = [
        migrations.RunPython(populate_permissions)
    ]
