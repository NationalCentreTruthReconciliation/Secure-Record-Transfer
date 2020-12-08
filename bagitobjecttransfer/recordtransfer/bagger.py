''' Facilitates creating BagIt bags and writing them to disk. '''
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
        LOGGER.error(msg=('Could not find storage folder "{0}"'.format(storage_folder)))
        raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')

    LOGGER.info(msg=('Starting new bag creation for upload session "{0}"'.format(session_token)))

    current_time = timezone.now()
    identifier = bag_identifier or current_time.strftime(r'%Y%m%d_%H%M%S')

    new_bag_folder = _get_bagging_folder(storage_folder, identifier)
    if not new_bag_folder.exists():
        os.mkdir(new_bag_folder)
        LOGGER.info(msg=('Created new empty folder for the bag at "{0}"'.format(new_bag_folder)))

    (copied_files, missing_files) = _copy_session_uploads_to_dir(session_token, new_bag_folder, deletefiles)

    bag_valid = False # Invalid until proven otherwise!
    if not missing_files:
        LOGGER.info(msg=('Generating sha512 checksums...'))
        bag = bagit.make_bag(new_bag_folder, metadata, checksums=['sha512'])
        LOGGER.info(msg=('Checking validity of new bag...'))
        bag_valid = bag.is_valid()
        if bag_valid:
            # Fix permissions of payload files (make_bag sometimes makes files unreadable)
            for payload_file in bag.payload_files():
                payload_file_path = new_bag_folder / payload_file
                os.chmod(payload_file_path, 0o644)
            LOGGER.info(msg=('New bag successfully created at "{0}"'.format(new_bag_folder)))
        else:
            LOGGER.error(msg=('New bag created at "{0}" is invalid!'.format(new_bag_folder)))
    else:
        LOGGER.error(msg=('New bag "{0}" was not created due to these files missing: {1}'.format(
            new_bag_folder, missing_files)))
        LOGGER.info(msg=('Removing half-created bag at {0}'.format(new_bag_folder)))
        for copied_file in copied_files:
            os.remove(copied_file)
        if new_bag_folder.exists():
            os.rmdir(new_bag_folder)

    bag_was_created = bool(not missing_files)

    return {
        'missing_files': missing_files,
        'bag_created': bag_was_created,
        'bag_valid': bag_valid,
        'time_created': current_time if bag_was_created else None,
        'bag_location': str(new_bag_folder) if bag_was_created else None,
    }


def update_bag(bag_folder: str, metadata: dict):
    """ Updates the metadata for a bag located at the folder. The integrity of the bag is checked
    before updating; if the bag is invalid, the bag will not be updated.

    Args:
        bag_folder (str): The bag folder to be updated
        metadata (dict): The metadata fields to update in bag-info.txt

    Returns:
        (dict): A dictionary containing update information.
    """
    if not Path(bag_folder).exists():
        LOGGER.error(msg=('There is no bag located at "{0}"!'.format(bag_folder)))
        return {'bag_exists': False, 'bag_updated': False, 'num_fields_updated': 0}

    bag = bagit.Bag(bag_folder)
    if not bag.is_valid():
        LOGGER.error(msg=('The bag located at "{0}" was found to be invalid!'.format(bag_folder)))
        return {'bag_exists': True, 'bag_valid': False, 'num_fields_updated': 0}

    if not metadata:
        LOGGER.info(msg=('No updates were made to the bag-info.txt for the bag at '
                         '"{0}"'.format(bag_folder)))
        return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': 0}

    LOGGER.info(msg=('Updating bag-info.txt for the bag at "{0}"'.format(bag_folder)))
    fields_updated = 0
    for key, new_value in metadata.items():
        if key not in bag.info:
            LOGGER.info(msg=('New fields cannot be added to a bag. Found invalid field '
                             '"{0}"'.format(key)))
        elif bag.info[key] != new_value:
            bag.info[key] = new_value
            fields_updated += 1

    if fields_updated == 0:
        LOGGER.info(msg=('No updates were made to the bag-info.txt file for the bag at '
                         '"{0}"'.format(bag_folder)))
        return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': fields_updated}

    # Don't re-create manifest for files, only for bag-info
    bag.save(manifests=False)

    if not bag.is_valid():
        LOGGER.error(msg=('Made {0} updates to the bag-info.txt file for the bag at "{1}", but '
                          'the saved bag was invalid!'.format(fields_updated, bag_folder)))
        return {'bag_exists': True, 'bag_valid': False, 'num_fields_updated': fields_updated}

    LOGGER.info(msg=('Made {0} updates to the bag-info.txt file for the bag at '
                     '"{1}"'.format(fields_updated, bag_folder)))
    return {'bag_exists': True, 'bag_valid': True, 'num_fields_updated': fields_updated}


def delete_bag(bag_folder: str):
    """ Deletes a bag folder and all of its contents

    Args:
        bag_folder (str): The bag folder to be deleted
    """
    if not Path(bag_folder).exists():
        raise FolderNotFoundError(f'Could not find folder "{bag_folder}"')
    LOGGER.info(msg=('Deleting the bag at "{0}"'.format(bag_folder)))
    shutil.rmtree(bag_folder)


def _copy_session_uploads_to_dir(session_token, directory, delete=True):
    files = UploadedFile.objects.filter(
        session__token=session_token
    ).filter(
        old_copy_removed=False
    )

    LOGGER.info(msg=('Copying {0} temp files to {1}'.format(len(files), directory)))
    copied_files = []
    missing_files = []
    verb = 'Moving' if delete else 'Copying'
    for uploaded_file in files:
        source_path = Path(uploaded_file.path)

        if not source_path.exists():
            LOGGER.error(msg=('File "{0}" was moved or deleted'.format(source_path)))
            missing_files.append(str(source_path))

        elif not missing_files:
            destination_path = directory / uploaded_file.name
            LOGGER.info(msg=('{0} {1} to {2}'.format(verb, source_path, destination_path)))
            shutil.copy2(source_path, destination_path)
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
