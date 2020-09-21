''' Facilitates creating BagIt bags and writing them to disk '''
from pathlib import Path
import logging
import os
import shutil

import bagit

from django.utils import timezone

from recordtransfer.models import UploadedFile
from recordtransfer.exceptions import FolderNotFoundError


LOGGER = logging.getLogger(__name__)


def create_bag(storage_folder: str, session_token: str, metadata: dict, bag_identifier=None,
               deletefiles=True):
    """ Creates a bag from a user upload session and any number of metadata fields.

    Creates a bag within the storage_folder. A bag consists of a bag folder, and a number of tag
    files, data files, and manifest files.

    Args:
        storage_folder (str): Path to folder to store the bag in.
        session_token (str): The UploadSession token corresponding to the uploaded files.
        metadata (dict): A dictionary of metadata fields to be written to bag-info.txt.
        bag_identifier (str): A string to identify the bag. If None, the time is used to identify
            the bag.
        deletefiles (bool): Delete files in upload session after bagging if True.
    """
    if not Path(storage_folder).exists():
        LOGGER.error(msg=('Bagger: Could not find storage folder "%s"' % storage_folder))
        raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')

    current_time = timezone.now()
    identifier = bag_identifier or current_time.strftime(r'%Y%m%d_%H%M%S')

    new_bag_folder = _get_bagging_folder(storage_folder, identifier)
    if not new_bag_folder.exists():
        os.mkdir(new_bag_folder)

    (copied_files, missing_files) = _copy_session_uploads_to_dir(session_token, new_bag_folder, deletefiles)

    if not missing_files:
        bag = bagit.make_bag(new_bag_folder, metadata, checksums=['sha512'])
        bag_valid = bag.is_valid()
        if bag_valid:
            LOGGER.info(msg=('Bag created at "%s"' % new_bag_folder))
        else:
            LOGGER.warning(msg=('Bag created at "%s" is invalid!' % new_bag_folder))
    else:
        for copied_file in copied_files:
            os.remove(copied_file)
        if new_bag_folder.exists():
            os.rmdir(new_bag_folder)
        LOGGER.info(msg=('Bag "%s" was not created due to files missing: %s' % new_bag_folder, missing_files))

    bag_was_created = bool(not missing_files)

    return {
        'missing_files': missing_files,
        'bag_created': bag_was_created,
        'time_created': current_time if bag_was_created else None,
        'bag_location': str(new_bag_folder) if bag_was_created else None,
    }


def delete_bag(bag_folder: str):
    """ Deletes a bag folder and all of its contents

    Args:
        bag_folder (str): The bag folder to be deleted
    """
    if not Path(bag_folder).exists():
        raise FolderNotFoundError(f'Could not find folder "{bag_folder}"')
    shutil.rmtree(bag_folder)


def _copy_session_uploads_to_dir(session_token, directory, delete=True):
    files = UploadedFile.objects.filter(
        session__token=session_token
    ).filter(
        old_copy_removed=False
    )

    copied_files = []
    missing_files = []
    for uploaded_file in files:
        source_path = Path(uploaded_file.path)

        if not source_path.exists():
            LOGGER.error(msg=('file "%s" does not exist' % source_path))
            missing_files.append(str(source_path))

        elif not missing_files:
            destination_path = directory / uploaded_file.name
            LOGGER.info(msg=('copying %s to %s' % (source_path, destination_path)))
            shutil.copy(source_path, destination_path)
            if delete:
                uploaded_file.delete_file()
            copied_files.append(str(destination_path))

    return (copied_files, missing_files)


def _get_bagging_folder(storage_folder: str, identifier: str):
    """ Creates a unique folder path to store bag contents in, incorporating the identifier string.

    Args:
        storage_folder (str): The parent folder to create a bagging folder in
        identifier (str): Identification string for bag

    Returns:
        pathlib.Path: A path to new, unique folder name containing the identifier
    """
    storage_folder_path = Path(storage_folder)

    if not Path(storage_folder_path).exists():
        raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')
    new_folder = storage_folder_path / f'Bag_{identifier}'
    increment = 1
    while new_folder.exists():
        new_folder = storage_folder_path / f'Bag_{identifier}_{increment}'
        increment += 1
    return new_folder
