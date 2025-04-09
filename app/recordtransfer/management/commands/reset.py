import contextlib
import json
import os
import shutil
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command to reset the database by removing and recreating the schema."""

    help = """Resets the database by completely removing the development database file and
    recreating schema"""

    def add_arguments(self, parser) -> None:
        """Add arguments for the command."""
        parser.add_argument(
            "--seed",
            action="store_true",
            help="""Populate the database with seed data and required uploaded files after
            resetting it.""",
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt before resetting the database.",
        )

    def handle(self, *args, **options) -> None:
        """Handle the command."""
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR(
                    "ERROR: 'reset' command not permitted in production environments."
                )
            )
            return

        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
            self.stdout.write(
                self.style.ERROR(
                    "ERROR: 'reset' command only works with SQLite3 databases."
                )
            )
            return

        verbosity = 1
        seed = options.get("seed", False)
        no_confirm = options.get("no_confirm", False)

        if not no_confirm:
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

        # Seed database and populate data if requested
        if seed:
            self.stdout.write(self.style.WARNING("Seeding database..."))
            call_command("loaddata", "seed_data", verbosity=verbosity)
            self.stdout.write(self.style.SUCCESS("Database seeded successfully"))

            self.stdout.write(self.style.WARNING("Setting up uploaded files..."))
            success = self.setup_uploaded_files()
            if success:
                self.stdout.write(self.style.SUCCESS("Uploaded files setup successfully"))
            else:
                self.stdout.write(self.style.ERROR("Failed to set up uploaded files"))

    def setup_uploaded_files(self) -> bool:
        """Copy the files specified in seed_data.json to the appropriate locations
        for both temporary and permanent uploaded files.

        Returns: True if successful, False otherwise.
        """
        seed_data_path = Path(settings.BASE_DIR) / "fixtures" / "seed_data.json"

        try:
            with open(seed_data_path, "r") as file:
                seed_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.stdout.write(self.style.ERROR(f"Error loading seed data: {e!s}"))
            return False

        try:
            # Find file models and create the files on the file system
            for model in seed_data:
                model_name = model["model"]
                if model_name in (
                    "recordtransfer.tempuploadedfile",
                    "recordtransfer.permuploadedfile",
                ):
                    self.setup_uploaded_file(model)
        except Exception:
            return False
        return True

    def setup_uploaded_file(self, model: dict) -> None:
        """Set up the uploaded file in the appropriate location based on the model type."""
        source_file = Path(settings.BASE_DIR) / "fixtures" / model["fields"]["name"]
        if not source_file.exists():
            self.stdout.write(self.style.ERROR(f"Source file not found: {source_file}"))
            raise FileNotFoundError(
                f"Source file not found: {source_file}"
            )

        # Setup target path
        token = Path(model["fields"]["file_upload"]).parts[0]
        storage_folder = (
            settings.TEMP_STORAGE_FOLDER
            if model["model"] == "recordtransfer.tempuploadedfile"
            else settings.UPLOAD_STORAGE_FOLDER
        )
        target = Path(storage_folder) / token / model["fields"]["name"]

        # Ensure directories exist
        os.makedirs(target.parent, exist_ok=True)

        # Copy file
        try:
            shutil.copy2(source_file, target)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error copying file: {e!s}"))
            raise e
