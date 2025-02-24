from argparse import ArgumentParser

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Set the domain of the current site."""

    INVALID_PREFIXES = ("http:", "https:")

    help = "Sets the domain of the current site"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add arguments to the command."""
        parser.add_argument(
            "domain",
            type=str,
            help='The domain to set for the current site (e.g., "https://my.domain.com")',
        )
        parser.add_argument(
            "--display-name",
            type=str,
            help="Optional display name to set for the current site",
            default=None,
        )

    def handle(self, *args, **options) -> None:
        """Set the domain of the current site."""
        domain = options["domain"]
        display_name = options["display_name"]

        if any(domain.startswith(prefix) for prefix in Command.INVALID_PREFIXES):
            self.stdout.write(
                self.style.WARNING(
                    "Domain should not start with any of the following prefixes: "
                    f"{', '.join(Command.INVALID_PREFIXES)}"
                )
            )
            return

        if any(c.isspace() for c in domain):
            self.stdout.write(
                self.style.WARNING("Domain should not contain whitespace")
            )
            return

        current_site = Site.objects.get_current()

        current_site.domain = domain

        if display_name:
            current_site.name = display_name

        current_site.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set domain to "{domain}" for site "{current_site.name}"'
            )
        )
