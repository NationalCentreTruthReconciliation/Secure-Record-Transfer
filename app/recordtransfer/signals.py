from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured


def verify_site_id(sender, **kwargs):
    """Verify that the SITE_ID setting is valid."""
    site_id = settings.SITE_ID
    if not Site.objects.filter(pk=site_id).exists():
        raise ImproperlyConfigured(f"Site with ID {site_id} does not exist.")
