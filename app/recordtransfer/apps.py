import logging

from django.apps import AppConfig

LOGGER = logging.getLogger("recordtransfer")


class RecordTransferConfig(AppConfig):
    """Top-level application config for the recordtransfer app."""

    name = "recordtransfer"

    def ready(self) -> None:
        """Import signal handlers when Django starts."""
        from django.contrib.auth.signals import user_logged_in

        from recordtransfer.signals import add_logged_in_flag

        user_logged_in.connect(add_logged_in_flag)
