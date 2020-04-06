""" Functions for cleaning up old files, etc. """

from datetime import datetime, timedelta
from recordtransfer.models import UploadedFile

class Cleaner:
    @staticmethod
    def remove_old_uploads(hours=12):
        """ Deletes every file tracked in the database older than a specified number of hours.

        Args:
            hours (int): The threshold number of hours in the past required to delete a file
        """
        time_threshold = datetime.now() - timedelta(hours=hours)

        old_undeleted_files = UploadedFile.objects.filter(
            old_copy_removed=False
        ).filter(
            session__started_at__lt=time_threshold
        )

        print('Running cleaning')

        for upload in old_undeleted_files:
            upload.delete_file()
