from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Set the domain of the current site."""

    help = "Sets the domain of the current site"

    def add_arguments(self, parser) -> None:
        """Add arguments to the command."""
        parser.add_argument(
            "domain",
            type=str,
            help='The domain to set for the current site (e.g., "https://my.domain.com")',
        )

    def handle(self, *args, **options) -> None:
        """Set the domain of the current site."""
        domain = options["domain"]

        # Get the current site
        current_site = Site.objects.get_current()

        # Check if domain is already set
        if current_site.domain == domain:
            self.stdout.write(
                self.style.WARNING(f'Domain is already set to "{domain}"')
            )
            return

        # Update the domain
        current_site.domain = domain
        current_site.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set domain to "{domain}" for site "{current_site.name}"'
            )
        )
