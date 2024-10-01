#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from decouple import config


def initialize_debugger():
    ''' Start debugging if these conditions are met:

    - The Django DEBUG setting is True
    - The ENABLE_DEBUGPY environment variable is "1"
    - This is the main Django process (i.e., this is not the reloader process
      Django runs to check for code changes - RUN_MAIN is checked for this
      condition)
    - This is a "runserver" command or other command set by the variable
      "ENABLE_DEBUGPY_ON_COMMAND". This is to avoid clashing with other
      manage.py commands like migrate or shell or makemigrations.

    You may also set the port debugpy uses. Otherwise, the port 8009 is used.

    See below for info related to RUN_MAIN:
    - https://stackoverflow.com/a/73437126
    - https://stackoverflow.com/a/62944426
    '''
    from django.conf import settings

    if settings.DEBUG and \
        config('ENABLE_DEBUGPY', default='0') == '1' and \
        not os.getenv('RUN_MAIN'):

        command = config('ENABLE_DEBUGPY_ON_COMMAND', default='runserver')

        if command in sys.argv:
            import debugpy
            port = config('DEBUGPY_PORT', default=8009, cast=int)
            print(f'Attaching debugger to port {port}')
            debugpy.listen(('0.0.0.0', port))


def check_yuglify_binary():
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    if not os.path.exists(settings.YUGLIFY_BINARY):
        if settings.DEBUG:
            print(f"WARNING: yuglify could not be found at '{settings.YUGLIFY_BINARY}'. Did you "
                  "forget to execute 'npm run compile'?")
        else:
            raise ImproperlyConfigured(
                f"Could not find yuglify binary at '{settings.YUGLIFY_BINARY}'. Did you forget "
                "to execute 'npm run compile'?"
            )


def main():
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = config(
            "DJANGO_SETTINGS_MODULE",
            default="bagitobjecttransfer.settings.test",
        )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    initialize_debugger()

    from django.conf import settings

    if not settings.DEBUG:
        check_yuglify_binary()

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
