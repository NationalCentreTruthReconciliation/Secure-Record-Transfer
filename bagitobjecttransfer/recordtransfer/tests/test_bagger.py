from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, ANY

from bagit import Bag
from django.test import TestCase

from recordtransfer.exceptions import FolderNotFoundError
from recordtransfer.bagger import create_bag, update_bag, delete_bag


class CreateBagTests(TestCase):
    def setUp(self):
        self.mock_path_exists = patch.object(Path, 'exists').start()
        self.mock_now = patch('django.utils.timezone.now').start()
        self.mock_os_remove = patch('os.remove').start()
        self.mock_os_mkdir = patch('os.mkdir').start()
        self.mock_os_rmdir = patch('os.rmdir').start()
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

    def test_valid_bag_created(self):
        # Arrange
        creation_time = datetime(2020, 11, 1, 8, 30, 0, 0, timezone.utc)
        metadata = {'someData': '1'}
        session_token = '123456'
        bag_folder = Path('/folder')
        self.mock_path_exists.return_value = True
        self.mock_now.return_value = creation_time
        self.mock_get_bag_folder.return_value = bag_folder
        self.mock_copy_uploads.return_value = (['/folder/file_1', '/folder/file_2'], [])
        fake_bag = Mock(spec=Bag)
        self.mock_make_bag.return_value = fake_bag
        fake_bag.is_valid.return_value = True
        # Act
        result = create_bag('/', session_token, metadata, bag_identifier=None, deletefiles=True)
        # Assert
        self.assertEqual(result['time_created'], creation_time)
        self.assertTrue(result['bag_created'])
        self.assertTrue(result['bag_valid'])
        self.assertFalse(result['missing_files'])
        self.assertEqual(result['bag_location'], '/folder')
        self.mock_get_bag_folder.assert_called_with('/', ANY)
        self.mock_copy_uploads.assert_called_with(session_token, bag_folder, True)
        self.mock_make_bag.assert_called_with(bag_folder, metadata, checksums=['sha512'])

    def test_invalid_bag_created(self):
        # Arrange
        creation_time = datetime(2020, 11, 1, 8, 30, 0, 0, timezone.utc)
        metadata = {'someData': '1'}
        session_token = '123456'
        bag_folder = Path('/folder')
        self.mock_path_exists.return_value = True
        self.mock_now.return_value = creation_time
        self.mock_get_bag_folder.return_value = bag_folder
        self.mock_copy_uploads.return_value = (['/folder/file_1', '/folder/file_2'], [])
        fake_bag = Mock(spec=Bag)
        self.mock_make_bag.return_value = fake_bag
        fake_bag.is_valid.return_value = False
        # Act
        result = create_bag('/', session_token, metadata, bag_identifier=None, deletefiles=True)
        # Assert
        self.assertEqual(result['time_created'], creation_time)
        self.assertTrue(result['bag_created'])
        self.assertFalse(result['bag_valid'])
        self.assertFalse(result['missing_files'])
        self.assertEqual(result['bag_location'], '/folder')
        self.mock_get_bag_folder.assert_called_with('/', ANY)
        self.mock_copy_uploads.assert_called_with(session_token, bag_folder, True)
        self.mock_make_bag.assert_called_with(bag_folder, metadata, checksums=['sha512'])

    def test_missing_files(self):
        # Arrange
        creation_time = datetime(2020, 11, 1, 8, 30, 0, 0, timezone.utc)
        metadata = {'someData': '1'}
        session_token = '123456'
        bag_folder = Path('/folder')
        self.mock_path_exists.return_value = True
        self.mock_now.return_value = creation_time
        self.mock_get_bag_folder.return_value = bag_folder
        self.mock_copy_uploads.return_value = (['/folder/file_1'], ['/folder/file_2'])
        # Act
        result = create_bag('/', session_token, metadata, bag_identifier=None, deletefiles=True)
        # Assert
        self.assertIsNone(result['time_created'])
        self.assertFalse(result['bag_created'])
        self.assertFalse(result['bag_valid'])
        self.assertEqual(result['missing_files'], ['/folder/file_2'])
        self.assertIsNone(result['bag_location'], '/folder')
        self.mock_get_bag_folder.assert_called_with('/', ANY)
        self.mock_copy_uploads.assert_called_with(session_token, bag_folder, True)
        self.mock_os_remove.assert_any_call('/folder/file_1')
        self.mock_os_rmdir.assert_called_with(bag_folder)

    def tearDown(self):
        patch.stopall()
