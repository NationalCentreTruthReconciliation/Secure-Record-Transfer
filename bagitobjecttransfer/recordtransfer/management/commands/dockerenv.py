from collections import OrderedDict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


DEFAULT_VARIABLES=OrderedDict(
    SIGN_UP_ENABLED=True,
    ALLOW_BAG_CHANGES=True,
    BAG_STORAGE_FOLDER='/app/media/bags',
    UPLOAD_STORAGE_FOLDER='/app/media/uploaded_files',
    ARCHIVIST_EMAIL='archivist@localhost',
    MYSQL_ROOT_PASSWORD='root-pw',
    MYSQL_DATABASE='records-transfer-db',
    MYSQL_USER='records-user',
    MYSQL_PASSWORD='records-password',
)

class Command(BaseCommand):
    ''' Command to create a simple .dockerenv file
    '''

    help = 'Creates a simple .dockerenv file - not ALL variables can be set with this command!'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite .dockerenv if it exists',
        )
        parser.add_argument(
            '--stdout',
            action='store_true',
            help='Write .dockerenv to stdout',
        )
        parser.add_argument(
            '--disable-signup',
            action='store_true',
            help='Disable signing up, enabled by default',
        )
        parser.add_argument(
            '--disable-bag-changes',
            action='store_true',
            help='Disable changes to existing BagIt bags, enabled by default',
        )
        parser.add_argument(
            '--bag-storage-folder',
            dest='BAG_STORAGE_FOLDER',
            help=(
                'Custom path for BAG_STORAGE_FOLDER, defaults to ' + \
                DEFAULT_VARIABLES['BAG_STORAGE_FOLDER']
            ),
        )
        parser.add_argument(
            '--upload-storage-folder',
            dest='UPLOAD_STORAGE_FOLDER',
            help=(
                'Custom path for UPLOAD_STORAGE_FOLDER, defaults to ' + \
                DEFAULT_VARIABLES['UPLOAD_STORAGE_FOLDER']
            ),
        )
        parser.add_argument(
            '--archivist-email',
            dest='ARCHIVIST_EMAIL',
            help=(
                'Custom email for ARCHIVIST_EMAIL, defaults to ' + \
                DEFAULT_VARIABLES['ARCHIVIST_EMAIL']
            ),
        )
        parser.add_argument(
            '--mysql-root-password',
            dest='MYSQL_ROOT_PASSWORD',
            help=(
                'Custom password for MYSQL_ROOT_PASSWORD, defaults to ' + \
                DEFAULT_VARIABLES['MYSQL_ROOT_PASSWORD']
            ),
        )
        parser.add_argument(
            '--mysql-database',
            dest='MYSQL_DATABASE',
            help=(
                'Custom name for MYSQL_DATABASE, defaults to ' + \
                DEFAULT_VARIABLES['MYSQL_DATABASE']
            )
        )
        parser.add_argument(
            '--mysql-user',
            dest='MYSQL_USER',
            help=(
                'Custom username MYSQL_USER, defaults to ' + \
                DEFAULT_VARIABLES['MYSQL_USER']
            )
        )
        parser.add_argument(
            '--mysql-password',
            dest='MYSQL_PASSWORD',
            help=(
                'Custom password for MYSQL_PASSWORD, defaults to ' + \
                DEFAULT_VARIABLES['MYSQL_PASSWORD']
            )
        )

    def handle(self, *args, **options):
        ''' Create the .dockerenv file contents and write to .dockerenv or
        stdout, depending on arguments.
        '''

        path = Path(settings.BASE_DIR) / '.dockerenv'

        if not options['stdout'] and not options['force'] and path.exists():
            raise CommandError(
                'The file .dockerenv already exists, use --force to overwrite '
                'it'
            )

        docker_env = ['# environment variables for docker']

        for var_name, default_value in DEFAULT_VARIABLES.items():
            value = None
            if var_name == 'SIGN_UP_ENABLED':
                value = 'false' if options['disable_signup'] else 'true'
            elif var_name == 'ALLOW_BAG_CHANGES':
                value = 'false' if options['disable_bag_changes'] else 'true'
            else:
                value = options[var_name] or default_value
            docker_env.append(f'{var_name}={value}')

        if options['stdout']:
            for line in docker_env:
                print(line)
        else:
            if options['force'] and path.exists():
                self.stdout.write(self.style.WARNING('Overwriting .dockerenv file'))
            with open(path, 'w', encoding='utf-8') as dockerenv_file:
                for line in docker_env:
                    dockerenv_file.write(line)
                    dockerenv_file.write('\n')
            self.stdout.write(str(path))
