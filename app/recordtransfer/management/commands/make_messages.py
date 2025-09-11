from typing import ClassVar

from django.core.management.commands import makemessages

BASE_MSGMERGE_OPTIONS = makemessages.Command.msgmerge_options  # type: ignore


class Command(makemessages.Command):
    """Replace the native django-admin makemessages command to add the --no-fuzzy-matching option.

    Taken from https://github.com/speedy-net/speedy-net/blob/staging/speedy/core/base/management/commands/make_messages.py
    (referenced in https://code.djangoproject.com/ticket/10852#comment:19)
    """

    msgmerge_options: ClassVar[list[str]] = [*BASE_MSGMERGE_OPTIONS, "--no-fuzzy-matching"]
