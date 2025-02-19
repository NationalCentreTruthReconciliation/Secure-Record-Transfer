from django.core.management.base import BaseCommand

from recordtransfer.scheduler import schedule_cleanup_jobs


class Command(BaseCommand):
    help = 'Schedule upload session cleanup jobs'

    def handle(self, *args, **kwargs):
        schedule_cleanup_jobs()
        self.stdout.write(
            self.style.SUCCESS('Successfully scheduled cleanup jobs')
        )
