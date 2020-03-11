import bagit
import os
import shutil
from pathlib import Path
from datetime import datetime


class FolderNotFoundError(Exception):
    pass


class Bagger:
    @staticmethod
    def create_bag(storage_folder: str, files: list, metadata: dict, deletefiles=False):
        """ Creates a bag from a list of file paths and a dictionary of bag metadata.

        Creates a bag within the storage_folder. A bag consists of a bag folder, and a number of tag
        files, data files, and manifest files. The bagit-py library is used, which has been developed
        by the Library of Congress.

        Args:
            storage_folder (str): Path to folder to store the bag in
            files (list): A list of dictionaries containing the path and the name of the files to be
                put in the bag. Each dictionary must have a 'filepath' field and a 'name' field.
            metadata (dict): A dictionary of bag metadata to be applied to bag tag files
        """
        if not Path(storage_folder).exists():
            raise FolderNotFoundError(f'Could not find folder "{storage_folder}"')

        new_bag_folder = Bagger._get_bagging_folder(storage_folder)
        if not new_bag_folder.exists():
            os.mkdir(new_bag_folder)

        missing_files = []
        copied_files = []

        for file_info in files:
            source_path = Path(file_info['filepath'])

            if not source_path.exists():
                print (f'Bagging ERROR: File "{source_path}" does not exist!')
                missing_files.append(str(source_path))

            elif not missing_files:
                destination_path = new_bag_folder / file_info['name']
                print (f'Bagging INFO: copying {source_path} to {destination_path}')
                if deletefiles:
                    shutil.move(source_path, destination_path)
                else:
                    shutil.copy(source_path, destination_path)
                copied_files.append(destination_path)

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

        return {
            'missing_files': missing_files,
            'bag_valid': bag_valid,
            'bag_created': bag_created,
            'bag_location': str(new_bag_folder) if bag_created else None
        }


    @staticmethod
    def delete_bag(self, bag_folder: str):
        """ Deletes a bag folder and all of its contents

        Args:
            bag_folder (str): The bag folder to be deleted
        """
        if not Path(bag_folder).exists():
            raise FolderNotFoundError(f'Could not find folder "{bag_folder}"')
        shutil.rmtree(bag_folder)


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
