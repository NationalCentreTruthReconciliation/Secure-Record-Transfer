import os
import re
import time

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand, CommandParser, CommandError


class Command(BaseCommand):
    ''' Wait for the database to become available '''

    help = 'Waits for the default database to be available before returning'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--max-retries', type=int, default=5, metavar='TIMES', help=(
            'max number of times to retry db connection before failing (default: 5)'
        ))
        parser.add_argument('--retry-interval', type=int, default=5, metavar='SECONDS', help=(
            'number of seconds to wait between retries (default: 5)'
        ))

    def handle(self, *args, **options):
        interval = options['retry_interval']
        max_retries = options['max_retries']

        engine = settings.DATABASES['default']['ENGINE']

        if 'sqlite3' in engine:
            db_path = settings.DATABASES['default']['NAME']
            filename = os.path.basename(db_path)

            db_info = f'{filename} database'

        else:
            name = settings.DATABASES['default'].get('NAME', '?')
            host = settings.DATABASES['default'].get('HOST', '?')
            port = settings.DATABASES['default'].get('PORT', '?')
            username = settings.DATABASES['default'].get('USER', '?')

            db_info = f'{name} database at {host}:{port} as {username}'

        db_conn = None

        attempts = 0
        while not db_conn and attempts < max_retries:
            try:
                self.stdout.write(f'Waiting for connection to {db_info} ...')
                connection.ensure_connection()
                db_conn = True

            except OperationalError:
                if interval == 1:
                    self.stdout.write(self.style.WARNING(f'Database unavailable, waiting {interval} seconds ...'))
                time.sleep(interval)

            finally:
                attempts += 1

        if db_conn:
            self.stdout.write(self.style.SUCCESS('Database connection established'))
        else:
            raise CommandError('Database connection could not be established!')
