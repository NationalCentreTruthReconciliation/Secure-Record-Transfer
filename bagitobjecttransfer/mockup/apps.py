from pathlib import Path

from django.apps import AppConfig

from mockup.appsettings import BAG_STORAGE_FOLDER


class MockupConfig(AppConfig):
    name = 'mockup'

    def ready(self):
        bagging_area = Path(BAG_STORAGE_FOLDER)
        if not bagging_area.exists():
            print(f'WARNING: Bag storage folder "{BAG_STORAGE_FOLDER}" does not exist!')
