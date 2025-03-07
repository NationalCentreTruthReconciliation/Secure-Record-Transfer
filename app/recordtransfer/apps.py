import logging

from django.apps import AppConfig

LOGGER = logging.getLogger("recordtransfer")


class RecordTransferConfig(AppConfig):
    """Top-level application config for the recordtransfer app."""

    name = "recordtransfer"
