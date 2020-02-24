import bagit
import os
import shutil
from pathlib import Path
from datetime import datetime

class FolderNotFoundError(Exception):
    pass

class Bagger:
    def __init__(self, bag_storage_folder):
        self.parent_folder = Path(bag_storage_folder)
        if not self.parent_folder.exists():
            raise FolderNotFoundError(f'Could not find folder "{bag_storage_folder}"')


    def create_bag(self, files, metadata):
        new_bag_folder = self._get_bagging_folder()
        if not new_bag_folder.exists():
            os.mkdir(new_bag_folder)

        missing_files = []
        copied_files = []
        for f in files:
            source_path = Path(f)
            if not source_path.exists():
                print (f'ERROR: File "{f}" does not exist!')
                missing_files.append(str(source_path))
            elif not missing_files:
                source_name = source_path.name
                destination_path = new_bag_folder / source_name
                print (f'INFO: copying {source_path} to {destination_path}')
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


    def delete_bag(self, bag_folder):
        shutil.rmtree(bag_folder)


    def _get_bagging_folder(self):
        current_date = datetime.today()
        time = datetime.strftime(current_date, r'%Y%m%d_%H%M%S')

        new_folder = self.parent_folder / f'Bag_{time}'
        folder_OK = False
        increment = 1
        while not folder_OK:
            if new_folder.exists():
                new_folder = self.parent_folder / f'Bag_{time}_{increment}'
                increment += 1
            else:
                folder_OK = True

        return new_folder
