from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase

from recordtransfer.exceptions import FolderNotFoundError
from recordtransfer.bagger import create_bag, update_bag, delete_bag
from recordtransfer.models import UploadSession, UploadedFile


class CreateBagTests(TestCase):
    def setUp(self):
        self.mock_path_exists = patch.object(Path, 'exists').start()
        self.mock_now = patch('django.utils.timezone.now').start()
        self.mock_os_remove = patch('os.remove').start()
        self.mock_os_mkdir = patch('os.mkdir').start()
        self.mock_make_bag = patch('bagit.make_bag').start()
        self.mock_copy_uploads = patch('recordtransfer.bagger._copy_session_uploads_to_dir').start()
        self.mock_get_bag_folder = patch('recordtransfer.bagger._get_bagging_folder').start()
        self.mock_logger = patch('recordtransfer.bagger.LOGGER').start()

    def test_bag_folder_does_not_exist(self):
        self.mock_path_exists.return_value = False
        self.assertRaises(FolderNotFoundError, create_bag, '/does/not/exist/', '123456', {})
        self.mock_logger.error.assert_called_with(
            msg='Could not find storage folder "/does/not/exist/"')
        self.assertFalse(self.mock_make_bag.called)

    def tearDown(self):
        patch.stopall()
