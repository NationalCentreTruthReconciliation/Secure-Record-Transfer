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

    def handle(self, *args, **options) -> None:
        """Handle the command."""
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR(
                    "ERROR: 'reset' command not permitted in production environments."
                )
            )
            return

        verbosity = 1
        create_seed = options.get("seed", False)

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
        if create_seed:
            self.stdout.write(self.style.WARNING("Seeding database..."))
            call_command("loaddata", "seed_data", verbosity=verbosity)
            self.stdout.write(self.style.SUCCESS("Database seeded successfully"))

            self.stdout.write(self.style.WARNING("Setting up uploaded files..."))
            self.setup_uploaded_files()
            self.stdout.write(self.style.SUCCESS("Uploaded files setup successfully"))

    def setup_uploaded_files(self) -> bool:
        """Copy the files specified in seed_data.json to the appropriate locations
        for both temporary and permanent uploaded files.
        """
        seed_data_path = Path(settings.BASE_DIR) / "fixtures" / "seed_data.json"

        try:
            with open(seed_data_path, "r") as file:
                seed_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.stdout.write(self.style.ERROR(f"Error loading seed data: {e!s}"))
            return False

        temp_file_data = None
        perm_file_data = None

        for item in seed_data:
            if item.get("model") == "recordtransfer.tempuploadedfile":
                temp_file_data = item
            elif item.get("model") == "recordtransfer.permuploadedfile":
                perm_file_data = item

        if not temp_file_data or not perm_file_data:
            self.stdout.write(self.style.ERROR("Could not find file data in seed file"))
            return False

        temp_filename = temp_file_data["fields"]["name"]
        temp_path = temp_file_data["fields"]["file_upload"]

        perm_filename = perm_file_data["fields"]["name"]
        perm_path = perm_file_data["fields"]["file_upload"]

        temp_token = Path(temp_path).parts[0]
        perm_token = Path(perm_path).parts[0]

        source_file = Path(settings.BASE_DIR) / "fixtures" / temp_filename

        if not source_file.exists():
            self.stdout.write(self.style.ERROR(f"Source file not found: {source_file}"))
            return False

        temp_target_dir = Path(settings.TEMP_STORAGE_FOLDER) / temp_token
        temp_target_file = temp_target_dir / temp_filename

        perm_target_dir = Path(settings.UPLOAD_STORAGE_FOLDER) / perm_token
        perm_target_file = perm_target_dir / perm_filename

        os.makedirs(temp_target_dir, exist_ok=True)
        os.makedirs(perm_target_dir, exist_ok=True)

        try:
            shutil.copy2(source_file, temp_target_file)

            shutil.copy2(source_file, perm_target_file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error copying files: {e!s}"))
            return False

        return True
