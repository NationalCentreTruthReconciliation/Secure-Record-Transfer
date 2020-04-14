from datetime import datetime
from collections import OrderedDict
from bs4 import BeautifulSoup
import logging

LOGGER = logging.getLogger(__name__)
DEFAULT_REPOSITORY = 'NCTR'


class TagGenerator:
    @staticmethod
    def generate_tags_from_form(cleaned_form_data: dict):
        # TODO: Maybe we should catch KeyErrors here and log those
        section_1 = get_section_1_identity_information(cleaned_form_data)
        section_2 = get_section_2_source_information(cleaned_form_data)
        section_3 = get_section_3_materials_information(cleaned_form_data)
        section_4 = get_section_4_management_information(cleaned_form_data)
        section_5 = get_section_5_event_information(cleaned_form_data)
        section_6 = get_section_6_general_information(cleaned_form_data)
        section_7 = get_section_7_control_information(cleaned_form_data)

        caais_tags = OrderedDict()
        caais_tags['identityInformation'] = section_1
        caais_tags['sourceInformation'] = section_2
        caais_tags['materialsInformation'] = section_3
        caais_tags['managementInformation'] = section_4
        caais_tags['eventInformation'] = section_5
        caais_tags['generalInformation'] = section_6
        caais_tags['controlInformation'] = section_7
        return caais_tags

def get_section_1_identity_information(cleaned_form_data: dict):
    identity_info = OrderedDict()
    identity_info['repository'] = DEFAULT_REPOSITORY
    identity_info['accessionIdentifier'] = ''
    identity_info['otherIdentifiers'] = []
    if 'formset-otheridentifiers' in cleaned_form_data:
        for other_id_form in cleaned_form_data['formset-otheridentifiers']:
            if not other_id_form:
                continue
            other_identifier = OrderedDict()
            other_identifier['otherIdentifierType'] = other_id_form['other_identifier_type']
            other_identifier['otherIdentifierValue'] = other_id_form['identifier_value']
            if 'identifier_note' in other_id_form:
                other_identifier['otherIdentifierNote'] = other_id_form['identifier_note']
            identity_info['otherIdentifiers'].append(other_identifier)
    else:
        LOGGER.warn(msg=('Did not find formset-otheridentifiers in cleaned form data'))
    identity_info['accessionTitle'] = cleaned_form_data['collection_title']
    identity_info['archivalUnit'] = ''
    identity_info['acquisitionMethod'] = 'Digital Transfer'
    return identity_info

def get_section_2_source_information(cleaned_form_data: dict):
    source_info = OrderedDict()
    source_info['sourceOfMaterial'] = OrderedDict()
    source_info['sourceOfMaterial']['sourceType'] = cleaned_form_data['source_type']
    source_info['sourceOfMaterial']['sourceName'] = cleaned_form_data['source_name']
    source_info['sourceOfMaterial']['sourceContactInformation'] = OrderedDict()
    source_info['sourceOfMaterial']['sourceContactInformation']['contactName'] = cleaned_form_data['contact_name']
    source_info['sourceOfMaterial']['sourceContactInformation']['jobTitle'] = cleaned_form_data['job_title']
    source_info['sourceOfMaterial']['sourceContactInformation']['phoneNumber'] = cleaned_form_data['phone_number']
    source_info['sourceOfMaterial']['sourceContactInformation']['emailAddress'] = cleaned_form_data['email']
    source_info['sourceOfMaterial']['sourceContactInformation']['addressLine1'] = cleaned_form_data['address_line_1']
    source_info['sourceOfMaterial']['sourceContactInformation']['addressLine2'] = cleaned_form_data['address_line_2']
    source_info['sourceOfMaterial']['sourceContactInformation']['provinceOrState'] = cleaned_form_data['province_or_state']
    source_info['sourceOfMaterial']['sourceContactInformation']['postalOrZipCode'] = cleaned_form_data['postal_or_zip_code']
    source_info['sourceOfMaterial']['sourceContactInformation']['country'] = cleaned_form_data['country']
    source_info['sourceOfMaterial']['sourceRole'] = cleaned_form_data['source_role']
    source_info['sourceOfMaterial']['sourceNote'] = cleaned_form_data['source_note']
    source_info['custodialHistory'] = cleaned_form_data['custodial_history']
    return source_info

def get_section_3_materials_information(cleaned_form_data: dict):
    materials_info = OrderedDict()
    if cleaned_form_data['start_date_is_approximate']:
        start_date = f'[ca. {cleaned_form_data["start_date_of_material"]}]'
    else:
        start_date = cleaned_form_data['start_date_of_material']
    if cleaned_form_data['end_date_is_approximate']:
        end_date = f'[ca. {cleaned_form_data["end_date_of_material"]}]'
    else:
        end_date = cleaned_form_data['end_date_of_material']
    materials_info['dateOfMaterial'] = f'{start_date} - {end_date}'
    materials_info['extentStatement'] = OrderedDict()
    materials_info['extentStatement']['extentStatementType'] = 'Extent received'
    materials_info['extentStatement']['quantityAndTypeOfUnits'] = 'WORK IN PROGRESS!'
    materials_info['scopeAndContent'] = cleaned_form_data['description']
    materials_info['languageOfMaterial'] = cleaned_form_data['language_of_material']
    return materials_info

def get_section_4_management_information(cleaned_form_data: dict):
    management_info = OrderedDict()
    management_info['storageLocation'] = 'WORK IN PROGRESS!'
    management_info['rightsStatement'] = []
    if 'formset-rights' in cleaned_form_data:
        for rights_form in cleaned_form_data['formset-rights']:
            if not rights_form:
                LOGGER.warn(msg=('Found empty rights form'))
                continue
            rights = OrderedDict()
            rights['rightsStatementType'] = rights_form['rights_type']
            rights['rightsStatementValue'] = rights_form['rights_statement']
            rights['rightsStatementNote'] = rights_form['rights_note']
            management_info['rightsStatement'].append(rights)
    else:
        LOGGER.warn(msg=('Did not find formset-rights in cleaned form data'))
    # Skipped Materials Assessment since digital object
    # Skipped Appraisal Statement
    # Skipped Associated Documentation

    return management_info

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


class DocumentGenerator:
    DEFAULT_CSS = '\n'.join([
    '  html {',
    '    font-family: "Segoe UI", Frutiger, "Frutiger Linotype" "Dejavu Sans", "Helvetica Neue", Arial, sans-serif !important;',
    '  }',
    '  .title {',
    '    font-size: 16pt;',
    '  }',
    '  @page {',
    '    size: A4;',
    '    margin: 0.5in 0.5in 0.5in 0.5in;',
    '  }',
    '  table {',
    '    min-width: 100%;',
    '  }',
    ])

    def __init__(self, caais_tags: OrderedDict):
        self.caais_tags = caais_tags
        self.document = []

    def generate_html_document(self):
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
        self._generate_section_1_markup()
        self.document.append('<br>')
        self._generate_section_2_markup()
        self.document.append('<br>')
        self._generate_section_3_markup()
        self.document.append('<br>')
        self._generate_section_4_markup()
        self.document.append('<br>')
        self._generate_section_5_markup()
        self.document.append('<br>')
        self._generate_section_6_markup()
        self.document.append('<br>')
        self._generate_section_7_markup()
        self.document.append('</body>')

    def _append_title_row(self, title: str):
        self.document.append(f'<tr><td colspan="2"><div class="title">{title}</div></td></tr>')

    def _append_normal_row(self, left_column: str, right_column: str):
        self.document.append(f'<tr><td>{left_column}</td><td>{right_column}</td></tr>')

    def _append_full_span_row(self, contents: str):
        self.document.append(f'<tr><td colspan="2"><b>{contents}</b></td></tr>')

    def _generate_section_1_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 1: Identity Information')
        self._append_normal_row('1.1 Repository',
            self.caais_tags['identityInformation']['repository'])
        self._append_normal_row('1.2 Accession Identifier',
            self.caais_tags['identityInformation']['accessionIdentifier'])

        num_other_identifiers = len(self.caais_tags['identityInformation']['otherIdentifiers'])
        for num, other_identifier in enumerate(self.caais_tags['identityInformation']['otherIdentifiers'], start=1):
            self._append_full_span_row(f'1.3 Other Identifier ({num} of {num_other_identifiers})')
            self._append_normal_row('1.3.1 Other Identifier Type', other_identifier['otherIdentifierType'])
            self._append_normal_row('1.3.2 Other Identifier Value', other_identifier['otherIdentifierValue'])
            if 'otherIdentifierNote' in other_identifier:
                self._append_normal_row('1.3.3 Other Identifier Note', other_identifier['otherIdentifierNote'])
        self.document.append('</table>')

    def _generate_section_2_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 2: Source Information')
        self._append_normal_row('1.1 Repository', 'NCTR')
        self.document.append('</table>')

    def _generate_section_3_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 3: Materials Information')
        self._append_normal_row('3.1 Repository', 'NCTR')
        self.document.append('</table>')

    def _generate_section_4_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 4: Management Information')
        self._append_normal_row('4.1 Repository', 'NCTR')
        self.document.append('</table>')

    def _generate_section_5_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 5: Event Information')
        self._append_normal_row('5.1 Repository', 'NCTR')
        self.document.append('</table>')

    def _generate_section_6_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 6: General Information')
        self._append_normal_row('6.1 Repository', 'NCTR')
        self.document.append('</table>')

    def _generate_section_7_markup(self):
        self.document.append('<table border="1" cellspacing="0">')
        self._append_title_row('Section 7: Control Information')
        self._append_normal_row('7.1 Repository', 'NCTR')
        self.document.append('</table>')
