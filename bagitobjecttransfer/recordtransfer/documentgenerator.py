from bs4 import BeautifulSoup
import logging
from recordtransfer.objectfromform import ObjectFromForm

LOGGER = logging.getLogger(__name__)

class HtmlDocument(ObjectFromForm):
    item_titles = {
        # Section 1
        'repository': '1.1 Repository',
        'accession_identifier': '1.2 Accession Identifier',
        'other_identifier': '1.3 Other Identifier',
        'other_identifier_type': '1.3.1 Other Identifier Type',
        'other_identifier_value': '1.3.2 Other Identifier Value',
        'other_identifier_note': '1.3.3 Other Identifier Note',
        'accession_title': '1.4 Accession Title',
        'archival_unit': '1.5 Archival Unit',
        'acquisition_method': '1.6 Acquisition Method',

        # Section 2
        'source_of_material': '2.1 Source Of Material',
        'source_type': '2.1.1 Source Type',
        'source_name': '2.1.2 Source Name',
        'source_contact_information': '2.1.3 Source Contact Information',
        'contact_name': 'Contact Name',
        'job_title': 'Job Title',
        'phone_number': 'Phone Number',
        'email': 'Email',
        'address_line_1': 'Address Line 1',
        'address_line_2': 'Address Line 2',
        'province_or_state': 'Province/State',
        'postal_or_zip_code': 'Postal/Zip Code',
        'country': 'Country',
        'source_role': '2.1.4 Source Role',
        'source_note': '2.1.5 Source Note',
        'custodial_history': '2.2 Custodial History',

        # Section 3
        'date_of_material': '3.1 Date of Material',
        'extent_statement': '3.2 Extent Statement',
        'extent_statement_type': '3.2.1 Extent Statement Type',
        'quantity_and_type_of_units': '3.2.2 Quantity and Type of Units',
        'extent_statement_note': '3.2.3 Extent Statement Note',
        'scope_and_content': '3.3 Scope and Content',
        'language_of_material': '3.4 Language of Material',

        # Section 4
        'storage_location': '4.1 Storage Location',
        'rights_statement': '4.2 Rights Statement',
        'rights_statement_type': '4.2.1 Rights Statement Type',
        'rights_statement_value': '4.2.2 Rights Statement Value',
        'rights_statement_note': '4.2.3 Rights Statement Note',
        'material_assessment_statement': '4.3 Materials Assessment Statement',
        'appraisal_statement': '4.4 Appraisal Statement',
        'associated_documentation': '4.5 Associated Documentation',

        # Section 5
        'event_statement': '5.1 Event Statement',
        'event_type': '5.1.1 Event Type',
        'event_date': '5.1.2 Event Date',
        'event_agent': '5.1.3 Event Agent',

        # Section 6
        'general_notes': '6.1 General Note',

        # Section 7
        'rules_or_conventions': '7.1 Rules or Conventions',
        'date_of_creation_or_revision': '7.3 Date of Creation or Revision',
        'action_type': '7.3.1 Action Type',
        'action_date': '7.3.2 Action Date',
        'action_agent': '7.3.3 Action Agent',
        'action_note': '7.3.4 Action Note',
    }

    DEFAULT_CSS = '\n'.join([
    '  .title {',
    '    font-size: 16pt;',
    '    font-weight: bold;',
    '  }',
    '  .left-col {',
    '    width: 33%;',
    '  }',
    '  @page {',
    '    size: A4;',
    '    margin: 0.5in 0.5in 0.5in 0.5in;',
    '  }',
    '  table {',
    '    min-width: 100%;',
    '    margin-top: 25px;',
    '  }',
    ])

    def __init__(self, form_data: dict):
        super().__init__(form_data)
        self.object = ''
        self.document = []

    def _pre_generation(self):
        self.document = []
        self.document.append('<!DOCTYPE html>')
        self.document.append('<head><style type="text/css"></style></head>')
        self.document.append('<body>')
        self.document.append('<h2>Record Transfer Document</h2>')

    def _pre_section_generation(self, **kwargs):
        section = kwargs.get('section')
        self.document.append(f'<table border="1" cellspacing="0" id="section_{section}">')

    def _post_generation(self):
        self.document.append('</body>')
        self.document.append('</html>')
        document_soup = BeautifulSoup('\n'.join(self.document), 'html.parser')
        document_soup.find('style').string = self.DEFAULT_CSS
        self.object = document_soup.prettify()

    def _post_section_generation(self, **kwargs):
        self.document.append('</table>')

    def _new_section(self, title):
        self.document.append(f'<tr><td colspan="2"><div class="title">{title}</div></td></tr>')

    def _new_item_collection(self, title, **kwargs):
        level = kwargs.get('level') if 'level' in kwargs else 1
        is_array_title = kwargs.get('is_array_title') if 'is_array_title' in kwargs else False
        index1 = kwargs.get('index1') if 'index1' in kwargs else -1
        total = kwargs.get('total') if 'total' in kwargs else -1

        row_title = f'{title} ({index1} of {total})' if is_array_title else title

        row = ['<tr><td colspan="2">']
        if level == 1:
            row.append(f'<b>{row_title}</b>')
        elif level == 2:
            row.append(row_title)
        elif level == 3:
            row.append(f'<i>{row_title}</i>')
        else:
            raise ValueError(f'Cannot create row with level {level}, can use 1, 2, or 3.')
        row.append('</td></tr>')
        self.document.append(''.join(row))

    def _new_item(self, title, data, **kwargs):
        level = kwargs.get('level') if 'level' in kwargs else 1

        row = ['<tr><td class="left-col">']
        if level == 1:
            row.append(f'<b>{title}</b></td>')
        elif level == 2:
            row.append(f'{title}</td>')
        elif level == 3:
            row.append(f'<i>{title}</i></td>')
        else:
            raise ValueError(f'Cannot create row with level {level}, can use 1, 2, or 3.')
        row.append(f'<td>{data}</td></tr>')
        self.document.append(''.join(row))
