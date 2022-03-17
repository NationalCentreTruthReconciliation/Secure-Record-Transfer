#pylint: disable=consider-using-f-string
import logging
import os
import re

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

from bagit import CHECKSUM_ALGOS

from recordtransfer import settings


LOGGER = logging.getLogger(__name__)


def verify_email_settings():
    ''' Verify the settings:

    - DO_NOT_REPLY_USERNAME
    - ARCHIVIST_EMAIL

    Throws an ImproperlyConfigured exception if either of these are empty.
    '''
    if not settings.DO_NOT_REPLY_USERNAME:
        raise ImproperlyConfigured(
            'The DO_NOT_REPLY_USERNAME setting is empty'
        )
    if not settings.ARCHIVIST_EMAIL:
        raise ImproperlyConfigured(
            'The ARCHIVIST_EMAIL setting is empty'
        )


def verify_date_format():
    ''' Verify the setting:

    - APPROXIMATE_DATE_FORMAT

    Throws an ImproperlyConfigured exception if the setting does not contain
    "{date}"
    '''
    if r'{date}' not in settings.APPROXIMATE_DATE_FORMAT:
        raise ImproperlyConfigured((
            'The APPROXIMATE_DATE_FORMAT (currently: {0}) does not contain '
            '{{date}}'
        ).format(settings.APPROXIMATE_DATE_FORMAT))


def verify_checksum_settings():
    ''' Verify the setting:

    - BAG_CHECKSUMS

    Throws an ImproperlyConfigured exception if the setting is not valid.
    '''
    if not settings.BAG_CHECKSUMS:
        raise ImproperlyConfigured(
            'No checksums found in the BAG_CHECKSUMS setting. Choose one '
            'or more checksum algorithms to generate checksums for when '
            'creating a BagIt bag, separated by commas (i.e., "sha1,sha256")'
        )
    not_found = [a for a in settings.BAG_CHECKSUMS if a not in CHECKSUM_ALGOS]
    if not_found:
        not_supported = ', '.join(not_found)
        supported = ', '.join(CHECKSUM_ALGOS)
        raise ImproperlyConfigured((
            'These algorithm(s) found in the BAG_CHECKSUMS setting are NOT '
            'supported: {0}. The algorithms that ARE supported are: {1}.'
        ).format(not_supported, supported))


def verify_storage_folder_settings():
    ''' Verify the settings:

    - BAG_STORAGE_FOLDER
    - UPLOAD_STORAGE_FOLDER

    Creates the directories if they do not exist. Raises an ImproperlyConfigured
    exception if the directories could not be created, or if they already exist
    but as file.
    '''
    for setting_name in [
            'BAG_STORAGE_FOLDER',
            'UPLOAD_STORAGE_FOLDER',
        ]:
        directory = getattr(settings, setting_name)

        if os.path.exists(directory) and os.path.isfile(directory):
            raise ImproperlyConfigured((
                'The {0} at {1} is a file. Remove this file or change the {0} '
                'to a different folder'
            ).format(setting_name, directory))

        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
                LOGGER.info('Created %s at %s', setting_name, directory)
            except PermissionError as exc:
                raise ImproperlyConfigured((
                    'Could not create the {0} at the path {1}. Ensure '
                    'permissions are configured so that this folder can be '
                    'created, or create it manually.'
                ).format(setting_name, directory)) from exc


def verify_max_upload_size():
    ''' Verify the settings:

    - MAX_TOTAL_UPLOAD_SIZE
    - MAX_SINGLE_UPLOAD_SIZE
    - MAX_TOTAL_UPLOAD_COUNT

    Throws an ImproperlyConfigured exception if any are less than or equal to
    zero, or if the single upload size is greater than the total upload size.
    '''
    for setting_name in [
            'MAX_TOTAL_UPLOAD_SIZE',
            'MAX_SINGLE_UPLOAD_SIZE',
            'MAX_TOTAL_UPLOAD_COUNT',
        ]:
        value = getattr(settings, setting_name)

        if not isinstance(value, int):
            raise ImproperlyConfigured((
                'The {0} setting is the wrong type (currently: {1}), should be '
                'int'
            ).format(setting_name, type(value)))

        if value == 0:
            raise ImproperlyConfigured((
                'The {0} setting is set to ZERO, it cannot be less than 1'
            ).format(setting_name))

        if value < 0:
            raise ImproperlyConfigured((
                'The {0} setting is negative (currently: {1}), it cannot be '
                'less than 1'
            ).format(setting_name, value))

    max_total_size = settings.MAX_TOTAL_UPLOAD_SIZE
    max_single_size = settings.MAX_SINGLE_UPLOAD_SIZE
    if max_total_size < max_single_size:
        raise ImproperlyConfigured((
            'The MAX_TOTAL_UPLOAD_SIZE setting (currently: {0}) cannot be less '
            'than the MAX_SINGLE_UPLOAD_SIZE setting (currently: {1})'
        ).format(max_total_size, max_single_size))


class RecordTransferConfig(AppConfig):
    ''' Top-level application config for the recordtransfer app
    '''

    name = 'recordtransfer'

    def ready(self):
        try:
            verify_email_settings()
            verify_date_format()
            verify_checksum_settings()
            verify_storage_folder_settings()
            verify_max_upload_size()

        except AttributeError as exc:
            match_obj = re.search(
                r'has no attribute ["\'](.+)["\']', str(exc), re.IGNORECASE
            )
            if match_obj:
                setting_name = match_obj.group(1)
                raise ImproperlyConfigured((
                    'The {0} setting is not defined in recordtransfer.settings!'
                ).format(setting_name)) from exc
            raise exc
