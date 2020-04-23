from datetime import datetime
from collections import OrderedDict
from bs4 import BeautifulSoup
import logging

LOGGER = logging.getLogger(__name__)

APPROXIMATE_DATE_FORMAT = '[ca. {date}]'
DEFAULT_REPOSITORY = 'NCTR'
DEFAULT_ARCHIVAL_UNIT = 'NCTR Archives'
DEFAULT_ACQUISITION_METHOD = 'Digital Transfer'
DEFAULT_STORAGE_LOCATION = 'Work in Progress'

class HtmlDocument:
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
        self.form_data = form_data
        self.document = []

    def get_document(self):
        self.document = []
        self.document.append('<!DOCTYPE html>')
        self.document.append('<head><style type="text/css"></style></head>')
        self._generate_body()
        self.document.append('</html>')
        document_soup = BeautifulSoup('\n'.join(self.document), 'html.parser')
        document_soup.find('style').string = self.DEFAULT_CSS
        return document_soup.prettify()

    def _generate_body(self):
        self.document.append('<body>')
        self.document.append('<h2>Record Transfer Document</h2>')
        self._generate_section_1_markup()
        self._generate_section_2_markup()
        self._generate_section_3_markup()
        self._generate_section_4_markup()
        #self._generate_section_5_markup()
        #self._generate_section_6_markup()
        #self._generate_section_7_markup()
        self.document.append('</body>')

    def _append_title_row(self, title: str):
        self.document.append(f'<tr><td colspan="2"><div class="title">{title}</div></td></tr>')

    def _append_normal_row(self, left_column: str, right_column: str, level=1):
        row = ['<tr><td class="left-col">']
        if level == 1:
            row.append(f'<b>{left_column}</b></td>')
        elif level == 2:
            row.append(f'{left_column}</td>')
        elif level == 3:
            row.append(f'<i>{left_column}</i></td>')
        else:
            raise ValueError(f'Cannot create row with level {level}, can use 1, 2, or 3.')
        row.append(f'<td>{right_column}</td></tr>')
        self.document.append(''.join(row))

    def _append_full_span_row(self, contents: str, level=1):
        row = ['<tr><td colspan="2">']
        if level == 1:
            row.append(f'<b>{contents}</b>')
        elif level == 2:
            row.append(contents)
        elif level == 3:
            self.document.append(f'<i>{contents}</i>')
        else:
            raise ValueError(f'Cannot create row with level {level}, can use 1, 2, or 3.')
        row.append('</td></tr>')
        self.document.append(''.join(row))

    def _start_new_table(self):
        self.document.append('<table border="1" cellspacing="0">')

    def _close_table(self):
        self.document.append('</table>')

    def _generate_section_1_markup(self):
        # TODO: Add checking for non-mandatory fields
        self._start_new_table()
        self._append_title_row('Section 1: Identity Information')
        self._append_normal_row('1.1 Repository', DEFAULT_REPOSITORY, level=1)
        self._append_normal_row('1.2 Accession Identifier', 'Work in Progress!', level=1)

        # Other identifier list
        other_identifiers_written = 0
        if 'formset-otheridentifiers' in self.form_data:
            num_other_identifiers = len(list(filter(None, self.form_data['formset-otheridentifiers'])))
            for num, other_id_form in enumerate(self.form_data['formset-otheridentifiers'], start=1):
                if not other_id_form:
                    continue
                self._append_full_span_row(f'1.3 Other Identifier ({num} of {num_other_identifiers})', level=1)
                self._append_normal_row('1.3.1 Other Identifier Type', other_id_form['other_identifier_type'], level=2)
                self._append_normal_row('1.3.2 Other Identifier Value', other_id_form['identifier_value'], level=2)
                if 'identifier_note' in other_id_form and other_id_form['other_identifier_note']:
                    self._append_normal_row('1.3.3 Other Identifier Note', other_id_form['identifier_note'], level=2)
                other_identifiers_written += 1

        if other_identifiers_written == 0:
            self._append_full_span_row('1.3 Other Identifiers: N/A', level=1)

        self._append_normal_row('1.4 Accession Title', self.form_data['collection_title'], level=1)
        self._append_normal_row('1.5 Archival Unit', DEFAULT_ARCHIVAL_UNIT, level=1)
        self._append_normal_row('1.6 Acqusition Method', DEFAULT_ACQUISITION_METHOD, level=1)
        self._close_table()

    def _generate_section_2_markup(self):
        # TODO: Add checking for non-mandatory fields
        self._start_new_table()
        self._append_title_row('Section 2: Source Information')
        self._append_full_span_row('2.1 Source of Material', level=1)
        self._append_normal_row('2.1.1 Source Type', self.form_data['source_type'], level=2)
        self._append_normal_row('2.1.2 Source Name', self.form_data['source_name'], level=2)
        self._append_full_span_row('2.1.3 Source Contact Information', level=2)
        self._append_normal_row('Contact Name', self.form_data['contact_name'], level=3)
        self._append_normal_row('Job Title', self.form_data['job_title'], level=3)
        self._append_normal_row('Phone Number', self.form_data['phone_number'], level=3)
        self._append_normal_row('Email Address', self.form_data['email'], level=3)
        self._append_normal_row('Address Line 1', self.form_data['address_line_1'], level=3)
        self._append_normal_row('Address Line 2', self.form_data['address_line_2'], level=3)
        self._append_normal_row('Province or State', self.form_data['province_or_state'], level=3)
        self._append_normal_row('Postal/Zip Code', self.form_data['postal_or_zip_code'], level=3)
        self._append_normal_row('Country', self.form_data['country'], level=3)
        self._append_normal_row('2.1.4 Source Role', self.form_data['source_role'], level=2)
        self._append_normal_row('2.1.5 Source Note', self.form_data['source_note'], level=2)
        self._append_normal_row('2.2 Custodial History', self.form_data['custodial_history'], level=1)
        self._close_table()

    def _generate_section_3_markup(self):
        # TODO: Add checking for non-mandatory fields
        if self.form_data['start_date_is_approximate']:
            start_date = APPROXIMATE_DATE_FORMAT.format(date=self.form_data["start_date_of_material"])
        else:
            start_date = self.form_data['start_date_of_material']
        if self.form_data['end_date_is_approximate']:
            end_date = APPROXIMATE_DATE_FORMAT.format(date=self.form_data["end_date_of_material"])
        else:
            end_date = self.form_data['end_date_of_material']

        self._start_new_table()
        self._append_title_row('Section 3: Materials Information')
        self._append_normal_row('3.1 Date of Material', f'{start_date} - {end_date}', level=1)
        self._append_full_span_row('3.2 Extent Statement', level=1)
        self._append_normal_row('3.2.1 Extent Statement Type', 'Extent received', level=2)
        self._append_normal_row('3.2.2 Quantity and Type of Units', 'Work in Progress.', level=2)
        self._append_normal_row('3.2.3 Extent Statement Note', 'Files counted automatically by application', level=2)
        self._append_normal_row('3.3 Scope and Content', self.form_data['description'], level=1)
        self._append_normal_row('3.4 Language of Material', self.form_data['language_of_material'], level=1)
        self._close_table()

    def _generate_section_4_markup(self):
        # TODO: Add checking for non-mandatory fields
        self._start_new_table()
        self._append_title_row('Section 4: Management Information')
        storage_location = self.form_data['storage_location'] if 'storage_location' in self.form_data \
            else DEFAULT_STORAGE_LOCATION
        self._append_normal_row('4.1 Storage Location', storage_location, level=1)

        rights_written = 0
        if 'formset-rights' in self.form_data and self.form_data['formset-rights']:
            num_rights = len(list(filter(None, self.form_data['formset-rights'])))
            for num, rights_form in enumerate(self.form_data['formset-rights'], start=1):
                if not rights_form:
                    LOGGER.warn(msg=('Found empty rights form'))
                    continue
                self._append_full_span_row(f'4.2 Rights Statement ({num} of {num_rights})', level=1)
                self._append_normal_row('4.2.1 Rights Statement Type', rights_form['rights_type'], level=2)
                self._append_normal_row('4.2.2 Rights Statement Value', rights_form['rights_statement'], level=2)
                if 'rights_note' in rights_form and rights_form['rights_note']:
                    self._append_normal_row('4.2.3 Rights Statement Note', rights_form['rights_note'], level=2)
                rights_written += 1
        else:
            LOGGER.warn(msg=('Did not find formset-rights in cleaned form data'))
        if rights_written == 0:
            LOGGER.warn(msg=('Did not find any valid rights forms in formset-rights in cleaned form data'))

        self._append_full_span_row('4.3 Material Assessment Statement: N/A', level=1)
        self._append_full_span_row('4.4 Appraisal Statement: N/A', level=1)
        self._append_full_span_row('4.5 Associated Documentation: N/A', level=1)
        self._close_table()

    '''
    def _generate_section_5_markup(self):
        self._start_new_table()
        self._append_title_row('Section 5: Event Information')
        total_events = len(self.caais_tags['eventInformation']['eventStatement'])
        for num, event in enumerate(self.caais_tags['eventInformation']['eventStatement'], start=1):
            self._append_full_span_row(f'5.1 Event ({num} of {total_events})', level=1)
            self._append_normal_row('5.1.1 Event Type', event['eventType'], level=2)
            self._append_normal_row('5.1.2 Event Date', event['eventDate'], level=2)
            self._append_normal_row('5.1.3 Event Agent', event['eventAgent'], level=2)
            if 'eventNote' in event:
                self._append_normal_row('5.1.4 Event Note', event['eventNote'], level=2)
        self._close_table()

    def _generate_section_6_markup(self):
        self._start_new_table()
        if 'generalInformation' in self.caais_tags and 'generalNote' in self.caais_tags['generalInformation']:
            self._append_title_row('Section 6: General Information')
            self._append_normal_row('6.1 General Note',
                self.caais_tags['generalInformation']['generalNote'])
        else:
            self._append_full_span_row('No general notes provided for Section 6')
        self._close_table()

    def _generate_section_7_markup(self):
        # TODO: Add checking for non-mandatory fields
        self._start_new_table()
        self._append_title_row('Section 7: Control Information')
        self._append_normal_row('7.1 Rules or Conventions',
            self.caais_tags['controlInformation']['rulesOrConventions'], level=1)
        total_dates = len(self.caais_tags['controlInformation']['dateOfCreationOrRevision'])
        for num, date in enumerate(self.caais_tags['controlInformation']['dateOfCreationOrRevision'], start=1):
            self._append_full_span_row(f'7.3 Date of Creation or Revision ({num} of {total_dates})', level=1)
            self._append_normal_row('7.3.1 Action Type', date['actionType'], level=2)
            self._append_normal_row('7.3.2 Action Date', date['actionDate'], level=2)
            self._append_normal_row('7.3.3 Action Agent', date['actionAgent'], level=2)
            if 'actionNote' in date:
                self._append_normal_row('7.3.4 Action Note', date['actionNote'], level=2)
        self._close_table()

def get_section_5_event_information(cleaned_form_data: dict):
    event_info = OrderedDict()
    event_info['eventStatement'] = []
    statement = OrderedDict()
    statement['eventType'] = 'Digital Object Transfer'
    statement['eventDate'] = datetime.now().strftime(r'%Y-%m-%d')
    statement['eventAgent'] = 'NCTR Record Transfer Portal'
    event_info['eventStatement'].append(statement)
    return event_info

def get_section_6_general_information(cleaned_form_data: dict):
    general_info = OrderedDict()
    general_info['generalNote'] = 'WORK IN PROGRESS!'
    return general_info

def get_section_7_control_information(cleaned_form_data: dict):
    control_info = OrderedDict()
    control_info['rulesOrConventions'] = 'Canadian Archival Accession Information Standards v1.0'
    control_info['dateOfCreationOrRevision'] = []
    creation_date = OrderedDict()
    creation_date['actionType'] = 'Created'
    creation_date['actionDate'] = datetime.now().strftime(r'%Y-%m-%d')
    creation_date['actionAgent'] = 'N/A'
    creation_date['actionNote'] = 'Created with NCTR Record Transfer Portal'
    control_info['dateOfCreationOrRevision'].append(creation_date)
    return control_info
    '''
