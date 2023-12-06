import time

import clamd

from clamav import settings
from clamav.connection import get_clamd_socket

from django.core.management.base import BaseCommand, CommandParser, CommandError


class Command(BaseCommand):
    ''' Wait for the database to become available '''

    help = 'Waits for clamav to be available (by pinging the service) before returning'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--max-retries', type=int, default=5, metavar='TIMES', help=(
            'max number of times to retry pinging ClamAV before failing (default: 5)'
        ))
        parser.add_argument('--retry-interval', type=int, default=5, metavar='SECONDS', help=(
            'number of seconds to wait between retries (default: 5)'
        ))

    def handle(self, *args, **options):
        interval = options['retry_interval']
        max_retries = options['max_retries']

        if not settings.CLAMAV_ENABLED:
            self.stdout.write(self.style.WARNING(
                'ClamAV is disabled (CLAMAV_ENABLED=False) - nothing to wait for'
            ))
            return

        host = settings.CLAMAV_HOST
        port = settings.CLAMAV_PORT

        self.stdout.write(f'Trying to establish connection to ClamAV at {host}:{port} ...')

        attempts = 0
        ping_success = False

        while not ping_success and attempts < max_retries:
            try:
                socket = get_clamd_socket()
                socket.ping()
                ping_success = True

            except clamd.ClamdError:
                self.stdout.write(self.style.WARNING(f'Connection not available, waiting {interval} seconds ...'))
                time.sleep(interval)

            finally:
                attempts += 1

        if ping_success:
            self.stdout.write(self.style.SUCCESS('ClamAV is available'))
        else:
            raise CommandError('A connection to ClamAV could not be established!')
