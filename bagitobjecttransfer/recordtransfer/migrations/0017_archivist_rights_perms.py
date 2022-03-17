from django.db import migrations
from django.core.management.sql import emit_post_migrate_signal
from django.contrib.auth.models import Group, Permission


def populate_permissions(apps, schema_editor):
    ''' Add permissions to edit rights to archivist staff '''
    emit_post_migrate_signal(1, False, 'default')
    group = Group.objects.get(name='archivist_user')
    existing_permissions = group.permissions.all()

    for codename in (
        # Rights
        'add_right',
        'change_right',
        'view_right'):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('recordtransfer', '0016_auto_20210528_1228'),
    ]

    operations = [
        migrations.RunPython(populate_permissions)
    ]
