import os
import shutil
from pathlib import Path
from datetime import datetime
import logging
import bagit

from recordtransfer.models import UploadedFile


LOGGER = logging.getLogger(__name__)


class FolderNotFoundError(Exception):
    pass


class Bagger:
    @staticmethod
    def create_bag(storage_folder: str, session_token: str, metadata: dict, deletefiles=True):
        """ Creates a bag from a list of file paths and a dictionary of bag metadata.

        Creates a bag within the storage_folder. A bag consists of a bag folder, and a number of tag
        files, data files, and manifest files. The bagit-py library is used, which has been
        developed by the Library of Congress.

        Args:
            storage_folder (str): Path to folder to store the bag in
            files (list): A list of dictionaries containing the path and the name of the files to be
                put in the bag. Each dictionary must have a 'filepath' field and a 'name' field.
            metadata (dict): A dictionary of bag metadata to be applied to bag tag files
        """
        if not Path(storage_folder).exists():
            LOGGER.error(msg=('Bagger: Could not find storage folder "%s"' % storage_folder))
            raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')

        new_bag_folder = Bagger._get_bagging_folder(storage_folder)
        if not new_bag_folder.exists():
            os.mkdir(new_bag_folder)

        (copied_files, missing_files) = Bagger.\
            _copy_session_uploads_to_dir(session_token, new_bag_folder, deletefiles)

        bag_valid = False
        bag_created = False
        if not missing_files:
            bag = bagit.make_bag(new_bag_folder, metadata, checksums=['sha256'])
            bag_valid = bag.is_valid()
            bag_created = True
        else:
            for copied_file in copied_files:
                os.remove(copied_file)
            if new_bag_folder.exists():
                os.rmdir(new_bag_folder)

        if bag_valid and bag_created:
            LOGGER.info(msg=('Bag created at "%s"' % new_bag_folder))
        else:
            LOGGER.info(msg=('Bag "%s" was not created' % new_bag_folder))

        return {
            'missing_files': missing_files,
            'bag_valid': bag_valid,
            'bag_created': bag_created,
            'bag_location': str(new_bag_folder) if bag_created else None
        }


    @staticmethod
    def delete_bag(bag_folder: str):
        """ Deletes a bag folder and all of its contents

        Args:
            bag_folder (str): The bag folder to be deleted
        """
        if not Path(bag_folder).exists():
            raise FolderNotFoundError(f'Could not find folder "{bag_folder}"')
        shutil.rmtree(bag_folder)


    @staticmethod
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


    @staticmethod
    def _get_bagging_folder(storage_folder: str) -> Path:
        """ Creates a unique, date-based folder path to store bag contents in

        Args:
            storage_folder (str): The parent folder to create a bagging folder in

        Returns:
            pathlib.Path: A path to new, unique folder name containing the current date
        """
        storage_folder_path = Path(storage_folder)

        if not Path(storage_folder_path).exists():
            raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')

        current_date = datetime.today()
        time = datetime.strftime(current_date, r'%Y%m%d_%H%M%S')

        new_folder = storage_folder_path / f'Bag_{time}'
        folder_OK = False
        increment = 1
        while not folder_OK:
            if new_folder.exists():
                new_folder = storage_folder_path / f'Bag_{time}_{increment}'
                increment += 1
            else:
                folder_OK = True

        return new_folder
