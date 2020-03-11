from django.apps import AppConfig

from .appsettings import BAG_STORAGE_FOLDER


class MockupConfig(AppConfig):
    name = 'mockup'

    def ready(self):
        from pathlib import Path
        bagging_area = Path(BAG_STORAGE_FOLDER)
        if not bagging_area.exists():
            print(f'WARNING: Bag storage folder "{BAG_STORAGE_FOLDER}" does not exist!')
