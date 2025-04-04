import contextlib
import os
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command to reset the database by removing and recreating the schema."""

    help = """Resets the database by completely removing the development database file and
    recreating schema"""

    def handle(self, *args, **options) -> None:
        # Prevent running in production environments
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR("ERROR: 'reset' command not permitted in production environments.")
            )
            return

        verbosity = options.get("verbosity", 1)

        self.stdout.write(
            self.style.WARNING("WARNING: This will delete ALL existing data in the database!")
        )
        confirm = input("Are you sure you want to proceed? (y/N): ")
        if confirm.lower() != "y":
            self.stdout.write(self.style.NOTICE("Operation cancelled."))
            return

        # Remove development database file if it exists
        if hasattr(settings, "DEV_DATABASE_NAME"):
            db_file = settings.DEV_DATABASE_NAME
            if os.path.exists(db_file):
                self.stdout.write(self.style.WARNING(f"Removing database file: {db_file}"))
                os.remove(db_file)
                self.stdout.write(self.style.SUCCESS("Database file removed"))
            else:
                self.stdout.write(self.style.NOTICE(f"Database file not found: {db_file}"))

        # Apply all migrations to recreate database
        self.stdout.write(self.style.WARNING("Recreating database schema..."))

        # Capture and suppress the migration output
        temp_stdout = StringIO()
        with contextlib.redirect_stdout(temp_stdout):
            call_command("migrate", interactive=False, verbosity=verbosity)

        self.stdout.write(self.style.SUCCESS("Database has been completely reset"))
