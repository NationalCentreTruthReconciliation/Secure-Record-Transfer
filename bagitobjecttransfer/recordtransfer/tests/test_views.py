from unittest.mock import patch
from pathlib import Path
import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from override_storage import override_storage
from override_storage.storage import LocMemStorage

from recordtransfer import settings
from recordtransfer.models import UploadSession, UploadedFile, User


TEST_FOLDER = Path(__file__).parent.resolve() / 'uploads'
if not TEST_FOLDER.exists():
    TEST_FOLDER.mkdir()


@patch('recordtransfer.settings.ACCEPTED_FILE_FORMATS', {
    'Document': ['docx', 'pdf'], 'Spreadsheet': ['xlsx']
})
@patch('recordtransfer.settings.MAX_TOTAL_UPLOAD_SIZE', 64) # MiB
@patch('recordtransfer.settings.MAX_SINGLE_UPLOAD_SIZE', 16) # MiB
@patch('recordtransfer.settings.MAX_TOTAL_UPLOAD_COUNT', 4) # Number of files
@override_storage(storage=LocMemStorage())
class TestAcceptFileView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls):
        cls.session_1 = UploadSession(
            token='test_session_1',
            started_at=timezone.now(),
        )
        cls.session_1.save()

        sixteen_mib = bytearray([1] * ((1024 ** 2) * 16))

        cls.uploaded_file_session_1_1 = UploadedFile(
            session=cls.session_1,
            file_upload=SimpleUploadedFile('File 1.docx', sixteen_mib),
            name='File 1.docx',
        )
        cls.uploaded_file_session_1_1.save()

        cls.uploaded_file_session_1_2 = UploadedFile(
            session=cls.session_1,
            file_upload=SimpleUploadedFile('File 2.docx', sixteen_mib),
            name='File 2.docx',
        )
        cls.uploaded_file_session_1_2.save()

        cls.uploaded_file_session_1_3 = UploadedFile(
            session=cls.session_1,
            file_upload=SimpleUploadedFile('File 3.pdf', sixteen_mib),
            name='File 3.pdf',
        )
        cls.uploaded_file_session_1_3.save()

        cls.uploaded_file_session_1_4 = UploadedFile(
            session=cls.session_1,
            file_upload=SimpleUploadedFile('File 4.xlsx', sixteen_mib),
            name='File 4.xlsx',
        )
        cls.uploaded_file_session_1_4.save()

        cls.session_2 = UploadSession(
            token='test_session_2',
            started_at=timezone.now(),
        )
        cls.session_2.save()

        cls.test_user_1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')

    def setUp(self):
        # Log in
        _ = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')

    def test_filename_missing(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filesize': '190',
        })
        self.assertEqual(response.status_code, 400)

    def test_file_name_empty(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': '',
            'filesize': '6123',
        })
        self.assertEqual(response.status_code, 400)

    def test_filesize_missing(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
        })
        self.assertEqual(response.status_code, 400)

    def test_filesize_empty(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
            'filesize': '',
        })
        self.assertEqual(response.status_code, 400)

    def test_filename_filesize_ok(self):
        param_list = [
            ('My File.pdf', '1'),
            ('My File.PDF', '1'),
            ('My File.PDf', '1'),
            ('My File.docx', '991'),
            ('My File.xlsx', '9081'),
        ]
        for filename, filesize in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': filename,
                    'filesize': filesize,
                })
                response_json = response.json()
                self.assertEqual(response_json['accepted'], True)

    def test_file_extension_not_okay(self):
        param_list = [
            'p',
            'mp3',
            'docxx',
        ]
        for extension in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': f'My File.{extension}',
                    'filesize': '9012',
                })
                response_json = response.json()
                self.assertEqual(response_json['accepted'], False)
                self.assertIn('extension', response_json['error'])

    def test_file_extension_missing(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File',
            'filesize': '209',
        })
        response_json = response.json()
        self.assertEqual(response_json['accepted'], False)
        self.assertIn('extension', response_json['error'])

    def test_invalid_size(self):
        param_list = [
            '-1',
            '-1000',
            'One thousand',
        ]
        for size in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': 'My File.pdf',
                    'filesize': size,
                })
                response_json = response.json()
                self.assertEqual(response_json['accepted'], False)
                self.assertIn('size is invalid', response_json['error'])

    def test_empty_file(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
            'filesize': '0',
        })
        response_json = response.json()
        self.assertEqual(response_json['accepted'], False)
        self.assertIn('empty', response_json['error'])

    def test_file_too_large(self):
        # Max size is patched to 16 MiB
        param_list = [
            (1024 ** 2) * 32, # 32 MiB
            ((1024 ** 2) * 16) + 1, # 16 MiB plus one byte
            (1024 ** 3), # 1 GiB
            (1024 ** 4), # 1 TiB
        ]
        for size in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': 'My File.pdf',
                    'filesize': size,
                })
                response_json = response.json()
                self.assertEqual(response_json['accepted'], False)
                self.assertIn('File is too big', response_json['error'])

    def test_file_exactly_max_size(self):
        # Max size is patched to 16 MiB
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
            'filesize': (1024 ** 2) * 16, # 16 MiB
        })
        response_json = response.json()
        self.assertEqual(response_json['accepted'], True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
