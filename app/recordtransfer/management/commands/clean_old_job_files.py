import argparse
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from recordtransfer.models import Job


class Command(BaseCommand):
    """Remove job attachment files older than a specified number of days (based on job.end_time)."""

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
