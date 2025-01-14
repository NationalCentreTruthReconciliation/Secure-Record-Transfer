#pylint: disable=too-many-public-methods
from unittest.mock import MagicMock, PropertyMock, patch
from pathlib import Path
import logging

from django.db.models.manager import BaseManager
from django.test import TestCase

from recordtransfer.models import UploadSession, UploadedFile


def get_mock_uploaded_file(name, exists=True, session=None, upload_to='/media/',
                           size=1024):
    ''' Create a new MagicMock that implements all the correct properties
    required for an UploadedFile
    '''
    if not exists:
        size = 0
    file_mock = MagicMock(spec=UploadedFile)
    path = upload_to.rstrip('/') + '/' + name
    type(file_mock).exists = PropertyMock(return_value=exists)
    type(file_mock).name = PropertyMock(return_value=name)
    type(file_mock).session = PropertyMock(return_value=session)
    type(file_mock.file_upload).size = PropertyMock(return_value=size)
    type(file_mock.file_upload).path = PropertyMock(return_value=path)
    type(file_mock.file_upload).name = PropertyMock(return_value=name)
    return file_mock


class TestUploadSession(TestCase):
    ''' Tests for the UploadSession model
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def test_empty_session(self):
        session = UploadSession.new_session()
        session.save()

        self.assertEqual(len(session.get_existing_file_set()), 0)
        self.assertEqual(session.upload_size, 0)

        session.delete()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_one_file_in_session(self, uploadedfile_set_mock):
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all.return_value = [
            get_mock_uploaded_file('1.pdf', size=1000),
        ]

        self.assertEqual(len(session.get_existing_file_set()), 1)
        self.assertEqual(session.upload_size, 1000)

        session.delete()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_multiple_files_in_session(self, uploadedfile_set_mock):
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all.return_value = [
            get_mock_uploaded_file('1.pdf', size=1000),
            get_mock_uploaded_file('2.pdf', size=1000),
            get_mock_uploaded_file('3.pdf', size=1000),
            get_mock_uploaded_file('4.pdf', size=1000),
            get_mock_uploaded_file('5.pdf', size=1000),
        ]

        self.assertEqual(len(session.get_existing_file_set()), 5)
        self.assertEqual(session.upload_size, 5000)

        session.delete()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_some_files_do_not_exist_in_session(self, uploadedfile_set_mock):
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all.return_value = [
            get_mock_uploaded_file('1.pdf', size=1000),
            get_mock_uploaded_file('2.pdf', size=1000),
            get_mock_uploaded_file('3.pdf', exists=False),
            get_mock_uploaded_file('4.pdf', exists=False),
        ]

        self.assertEqual(len(session.get_existing_file_set()), 2)
        self.assertEqual(session.upload_size, 2000)

        session.delete()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_delete_files_in_session(self, uploadedfile_set_mock):
        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file('1.pdf')
        file_2 = get_mock_uploaded_file('2.pdf')
        file_3 = get_mock_uploaded_file('3.pdf', exists=False)

        uploadedfile_set_mock.all.return_value = [file_1, file_2, file_3]

        session.remove_session_uploads()

        file_1.remove.assert_called_once()
        file_2.remove.assert_called_once()
        file_3.remove.assert_not_called()

        session.delete()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_move_files_in_session(self, uploadedfile_set_mock):
        mock_path_exists = patch.object(Path, 'exists').start()
        mock_path_exists.return_value = True

        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file('1.pdf')
        file_2 = get_mock_uploaded_file('2.pdf')
        file_3 = get_mock_uploaded_file('3.pdf', exists=False)

        uploadedfile_set_mock.all.return_value = [file_1, file_2, file_3]

        copied, missing = session.move_session_uploads('/home/')

        file_1.move.assert_called_once_with(Path('/home/1.pdf'))
        file_2.move.assert_called_once_with(Path('/home/2.pdf'))
        file_3.move.assert_not_called()
        self.assertIn(str(Path('/home/1.pdf')), copied)
        self.assertIn(str(Path('/home/2.pdf')), copied)
        self.assertEqual(len(missing), 1)

        session.delete()
        mock_path_exists.stop()

    @patch('recordtransfer.models.UploadSession.uploadedfile_set', spec=BaseManager)
    def test_copy_files_in_session(self, uploadedfile_set_mock):
        mock_path_exists = patch.object(Path, 'exists').start()
        mock_path_exists.return_value = True

        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file('1.pdf')
        file_2 = get_mock_uploaded_file('2.pdf')
        file_3 = get_mock_uploaded_file('3.pdf', exists=False)

        uploadedfile_set_mock.all.return_value = [file_1, file_2, file_3]

        copied, missing = session.copy_session_uploads('/home/')

        file_1.copy.assert_called_once_with(Path('/home/1.pdf'))
        file_2.copy.assert_called_once_with(Path('/home/2.pdf'))
        file_3.copy.assert_not_called()
        self.assertIn(str(Path('/home/1.pdf')), copied)
        self.assertIn(str(Path('/home/2.pdf')), copied)
        self.assertEqual(len(missing), 1)

        session.delete()
        mock_path_exists.stop()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
