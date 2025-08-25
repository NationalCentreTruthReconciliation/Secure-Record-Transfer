# Generated manually for loading admin interface theme

from django.core.management import call_command
from django.db import migrations


def load_admin_theme(apps, schema_editor):
    """Load the NCTR admin interface theme fixture."""
    call_command('loaddata', 'admin_interface_theme_nctr', verbosity=1)


def reverse_load_admin_theme(apps, schema_editor):
    """Remove the NCTR admin interface theme."""
    Theme = apps.get_model('admin_interface', 'Theme')
    Theme.objects.filter(name='NCTR').delete()


class Migration(migrations.Migration):
    dependencies = [  # noqa: RUF012
        ('recordtransfer', '0057_passwordhistory'),
        ('admin_interface', '__latest__'),
    ]

    operations = [  # noqa: RUF012
        migrations.RunPython(load_admin_theme, reverse_load_admin_theme),
    ]
