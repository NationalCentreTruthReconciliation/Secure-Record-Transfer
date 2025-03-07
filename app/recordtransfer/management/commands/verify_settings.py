import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

LOGGER = logging.getLogger("recordtransfer")


class Command(BaseCommand):
    """Verify application settings that require database access. Requires migrations to be
    run first.
    """

    help = "Verify application settings that require database access."

    def handle(self, *args, **options) -> None:
        """Verify application settings that require database access."""
        self.verify_site_id()

    def verify_site_id(self) -> None:
        """Verify that the SITE_ID setting is valid."""
        site_id = settings.SITE_ID
        if not Site.objects.filter(pk=site_id).exists():
            raise ImproperlyConfigured(
                f"Site with ID {site_id} does not exist. Check the configured SITE_ID"
            )
