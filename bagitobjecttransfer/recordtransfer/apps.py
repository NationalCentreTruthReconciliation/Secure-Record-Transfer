from pathlib import Path

from django.apps import AppConfig

from recordtransfer.appsettings import BAG_STORAGE_FOLDER

class RecordTransferConfig(AppConfig):
    name = 'recordtransfer'

    def ready(self):
        bagging_area = Path(BAG_STORAGE_FOLDER)
        if not bagging_area.exists():
            print(f'warning: bag storage folder "{BAG_STORAGE_FOLDER}" does not exist!')
