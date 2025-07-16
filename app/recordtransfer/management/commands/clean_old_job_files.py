import argparse
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from recordtransfer.models import Job


class Command(BaseCommand):
    """Remove job attachment files older than a specified number of days
    (based on job.end_time).
    """

    def add_arguments(self, parser: "argparse.ArgumentParser") -> None:
        """Add command-line arguments for the management command.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The parser to which arguments should be added.
        """
        parser.add_argument(
            "--older-than-days",
            type=int,
            required=True,
            help="Delete job attachment files for jobs whose end_time is older than this many days.",
        )

    def handle(self, *args, **options) -> None:
        """Delete job attachment files for jobs whose end_time is older than the
        specified number of days.

        Parameters
        ----------
        *args : tuple
            Variable length argument list.
        **options : dict
            Command-line options, expects 'older_than_days' key.

        Returns
        -------
        None
        """
        days = options["older_than_days"]
        cutoff = timezone.now() - timedelta(days=days)
        jobs = Job.objects.filter(end_time__lt=cutoff, attached_file__isnull=False)
        count = 0
        for job in jobs:
            if job.attached_file:
                file_path = job.attached_file.path
                job.attached_file.delete(save=True)
                self.stdout.write(f"Deleted: {file_path}")
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old job attachment file(s)."))
