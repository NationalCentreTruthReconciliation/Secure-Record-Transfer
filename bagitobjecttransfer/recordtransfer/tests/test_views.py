from unittest.mock import patch
import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from override_storage import override_storage
from override_storage.storage import LocMemStorage

from recordtransfer.models import UploadSession, UploadedFile, User


@patch('recordtransfer.settings.ACCEPTED_FILE_FORMATS', {
    'Document': ['docx', 'pdf'], 'Spreadsheet': ['xlsx']
})
@patch('recordtransfer.settings.MAX_TOTAL_UPLOAD_SIZE', 3) # MiB
@patch('recordtransfer.settings.MAX_SINGLE_UPLOAD_SIZE', 1) # MiB
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
        cls.one_mib = bytearray([1] * (1024 ** 2))
        cls.half_mib = bytearray([1] * int((1024 ** 2) / 2))
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
            ('My.File.PDf', '1024'),
            ('My File.docx', '991'),
            ('My File.xlsx', '9081'),
        ]
        for filename, filesize in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': filename,
                    'filesize': filesize,
                })
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertTrue(response_json['accepted'], True)

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
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json['accepted'])
                self.assertIn('extension', response_json['error'])

    def test_file_extension_missing(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File',
            'filesize': '209',
        })
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertFalse(response_json['accepted'])
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
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json['accepted'])
                self.assertIn('size is invalid', response_json['error'])

    def test_empty_file(self):
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
            'filesize': '0',
        })
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertFalse(response_json['accepted'])
        self.assertIn('empty', response_json['error'])

    def test_file_too_large(self):
        # Max size is patched to 1 MiB
        param_list = [
            (1024 ** 2) + 1, # 1 MiB plus one byte
            (1024 ** 2) * 8, # 8 MiB
            (1024 ** 2) * 32, # 32 MiB
            (1024 ** 3), # 1 GiB
            (1024 ** 4), # 1 TiB
        ]
        for size in param_list:
            with self.subTest():
                response = self.client.get(reverse('recordtransfer:checkfile'), {
                    'filename': 'My File.pdf',
                    'filesize': size,
                })
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json['accepted'])
                self.assertIn('File is too big', response_json['error'])

    def test_file_exactly_max_size(self):
        # Max size is patched to 1 MiB
        response = self.client.get(reverse('recordtransfer:checkfile'), {
            'filename': 'My File.pdf',
            'filesize': ((1024 ** 2) * 1), # 1 MiB
        })
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertTrue(response_json['accepted'])

    def test_session_has_room(self):
        files = []
        try:
            # 2 MiB of files (one MiB x 2)
            for name in ('File 1.docx', 'File 2.docx'):
                new_file =  UploadedFile(
                    session=self.session_1,
                    file_upload=SimpleUploadedFile(name, self.one_mib),
                    name=name,
                )
                new_file.save()
                files.append(new_file)

            for size in ('1024', len(self.one_mib)):
                with self.subTest():
                    response = self.client.post(reverse('recordtransfer:checkfile'), {
                        'filename': 'My File.pdf',
                        'filesize': size,
                    }, HTTP_Upload_Session_Token='test_session_1')
                    self.assertEqual(response.status_code, 200)
                    response_json = response.json()
                    self.assertTrue(response_json['accepted'])

        finally:
            for file_ in files:
                file_.delete()

    def test_session_file_count_full(self):
        files = []
        try:
            # 2 MiB of files (half MiB x 4)
            # Max file count is 4
            for name in ('File 1.docx', 'File 2.pdf', 'File 3.pdf', 'File 4.pdf'):
                new_file = UploadedFile(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, self.half_mib),
                )
                new_file.save()
                files.append(new_file)

            response = self.client.post(reverse('recordtransfer:checkfile'), {
                'filename': 'My File.pdf',
                'filesize': '1024',
            }, HTTP_Upload_Session_Token='test_session_1')

            self.assertEqual(response.status_code, 200)
            response_json = response.json()
            self.assertFalse(response_json['accepted'])
            self.assertIn('You can not upload anymore files', response_json['error'])

        finally:
            for file_ in files:
                file_.delete()

    def test_file_too_large_for_session(self):
        files = []
        try:
            # 2.5 MiB of files (1 Mib x 2, 0.5 MiB x 1)
            for name, content in (
                ('File 1.docx', self.one_mib),
                ('File 2.pdf', self.one_mib),
                ('File 3.pdf', self.half_mib)):
                new_file = UploadedFile(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, content),
                )
                new_file.save()
                files.append(new_file)

            response = self.client.post(reverse('recordtransfer:checkfile'), {
                'filename': 'My File.pdf',
                'filesize': len(self.one_mib),
            }, HTTP_Upload_Session_Token='test_session_1')

            self.assertEqual(response.status_code, 200)
            response_json = response.json()
            self.assertFalse(response_json['accepted'])
            self.assertIn('Maximum total upload size (3 MiB) exceeded', response_json['error'])

        finally:
            for file_ in files:
                file_.delete()

    def test_duplicate_file_name(self):
        files = []
        names = ('File.1.docx', 'File.2.pdf')
        try:
            for name in names:
                new_file = UploadedFile(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, self.half_mib),
                )
                new_file.save()
                files.append(new_file)

            for name in names:
                with self.subTest():
                    response = self.client.post(reverse('recordtransfer:checkfile'), {
                        'filename': name,
                        'filesize': '1024',
                    }, HTTP_Upload_Session_Token='test_session_1')

                    self.assertEqual(response.status_code, 200)
                    response_json = response.json()
                    self.assertFalse(response_json['accepted'])
                    self.assertIn('A file with the same name has already been uploaded',
                                  response_json['error'])

        finally:
            for file_ in files:
                file_.delete()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
