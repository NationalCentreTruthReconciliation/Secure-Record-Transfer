from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Remove job attachment files older than a specified number of days (based on job.end_time)."""
