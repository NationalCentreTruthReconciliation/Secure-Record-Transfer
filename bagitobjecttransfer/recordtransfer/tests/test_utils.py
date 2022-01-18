from django.test import TestCase
from recordtransfer.utils import get_human_readable_file_count, count_file_types, \
    snake_to_camel_case, html_to_text


class HtmlToTextTests(TestCase):
    def test_empty_string(self):
        text = html_to_text('')
        self.assertEqual(text, '')

    def test_simple_tag_removal(self):
        text = html_to_text('<h1>Hello</h1>')
        self.assertEqual(text, 'Hello')

    def test_nested_tags(self):
        text = html_to_text('<div><div><p>Hello</p></div></div>')
        self.assertEqual(text, 'Hello')

    def test_whitespace_stripped(self):
        html = '\n'.join([
            '',
            '<html>',
            '    <div> Hello  </div>',
            '    ',
            '</html>',
        ])
        text = html_to_text(html)
        self.assertEqual(text, 'Hello')


class SnakeToCamelCaseTests(TestCase):
    def test_empty_string(self):
        camel_case = snake_to_camel_case('')
        self.assertEqual(camel_case, '')

    def test_no_underscores(self):
        camel_case = snake_to_camel_case('encyclopedia')
        self.assertEqual(camel_case, 'encyclopedia')

    def test_with_underscores(self):
        camel_case = snake_to_camel_case('very_important_material')
        self.assertEqual(camel_case, 'veryImportantMaterial')


class FileCountingUtilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accepted_formats = {
            'Microsoft Word Document': [
                'doc',
                'docx',
            ],
            'Microsoft Excel Spreadsheet': [
                'xls',
                'xlsx',
            ],
            'Image': [
                'jpg',
                'png',
            ],
            'Audio': [
                'acc',
                'mp3',
            ],
        }

    '''
    def test_no_files_counted(self):
        counted_types = count_file_types(
            [],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {})

    def test_no_accepted_file_types(self):
        counted_types = count_file_types(
            ['file1.pages', 'file2.docs', 'file3.pdf'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {})

    def test_one_file_counted(self):
        counted_types = count_file_types(
            ['song1.mp3'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {'Audio': 1})

    def test_multiple_of_one_file_type_counted(self):
        counted_types = count_file_types(
            ['file1.doc', 'file2.doc', 'file3.docx'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {'Microsoft Word Document': 3})

    def test_multiple_different_files_counted(self):
        counted_types = count_file_types(
            ['file1.doc', 'file2.doc', 'song1.mp3', 'song1.acc', 'sheet1.xls', 'sheet2.xlsx'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {
            'Microsoft Word Document': 2,
            'Audio': 2,
            'Microsoft Excel Spreadsheet': 2,
        })

    def test_uppercase_extensions_are_counted(self):
        counted_types = count_file_types(
            ['file1.DOC', 'file2.doc', 'file3.docx', 'file4.DOCX'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {'Microsoft Word Document': 4})

    def test_unaccepted_files_ignored(self):
        counted_types = count_file_types(
            ['file1.pages', 'file2.docs', 'file3.pdf', 'file4.docx'],
            self.accepted_formats
        )
        self.assertEqual(counted_types, {'Microsoft Word Document': 1})

    def test_no_files_human_readable(self):
        statement = get_human_readable_file_count(
            [],
            self.accepted_formats
        )
        self.assertEqual(statement, 'No file types could be identified')

    def test_no_accepted_file_types_human_readable(self):
        statement = get_human_readable_file_count(
            ['file1.pages', 'file2.docs', 'file3.pdf'],
            self.accepted_formats
        )
        self.assertEqual(statement, 'No file types could be identified')

    def test_one_file_group_singular_human_readable(self):
        statement = get_human_readable_file_count(
            ['file1.DOC'],
            self.accepted_formats
        )
        self.assertEqual(statement, '1 Microsoft Word Document file')

    def test_one_file_group_plural_human_readable(self):
        statement = get_human_readable_file_count(
            ['file1.DOC', 'file2.doc', 'file3.docx', 'file4.DOCX'],
            self.accepted_formats
        )
        self.assertEqual(statement, '4 Microsoft Word Document files')

    def test_two_groups_human_readable(self):
        statement = get_human_readable_file_count(
            ['file1.DOC', 'file2.doc', 'song1.mp3', 'img1.jpg', 'img2.png', 'img3.png'],
            self.accepted_formats
        )
        self.assertIn('2 Microsoft Word Document files', statement)
        self.assertIn('1 Audio file', statement)
        self.assertIn('3 Image files', statement)
    '''
