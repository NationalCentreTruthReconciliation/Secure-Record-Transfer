import logging
from abc import ABC, abstractmethod
from collections import OrderedDict

from bs4 import BeautifulSoup

from django.utils import timezone

from recordtransfer.defaultdata import DEFAULT_DATA


LOGGER = logging.getLogger(__name__)


class ObjectFromForm(ABC):
    approximate_date_format = '[ca. {date}]'

    section_titles = {
        'section_1': 'Section 1: Identity Information',
        'section_2': 'Section 2: Source Information',
        'section_3': 'Section 3: Materials Information',
        'section_4': 'Section 4: Management Information',
        'section_5': 'Section 5: Event Information',
        'section_6': 'Section 6: General Information',
        'section_7': 'Section 7: Control Information',
    }

    item_titles = {
        # Section 1
        'repository': 'repository',
        'accession_identifier': 'accessionIdentifier',
        'other_identifier': 'otherIdentifier',
        'other_identifier_type': 'otherIdentifierType',
        'other_identifier_value': 'otherIdentifierValue',
        'other_identifier_note': 'otherIdentifierNote',
        'accession_title': 'accessionTitle',
        'archival_unit': 'archivalUnit',
        'acquisition_method': 'acquisitionMethod',

        # Section 2
        'source_of_material': 'sourceOfMaterial',
        'source_type': 'sourceType',
        'source_name': 'sourceName',
        'source_contact_information': 'sourceContactInformation',
        'contact_name': 'contactName',
        'job_title': 'jobTitle',
        'phone_number': 'phoneNumber',
        'email': 'email',
        'address_line_1': 'addressLine1',
        'address_line_2': 'addressLine2',
        'province_or_state': 'provinceOrState',
        'postal_or_zip_code': 'postalOrZipCode',
        'country': 'country',
        'source_role': 'sourceRole',
        'source_note': 'sourceNote',
        'custodial_history': 'custodialHistory',

        # Section 3
        'date_of_material': 'dateOfMaterial',
        'extent_statement': 'extentStatement',
        'extent_statement_type': 'extentStatementType',
        'quantity_and_type_of_units': 'quantityAndTypeOfUnits',
        'extent_statement_note': 'extentStatementNote',
        'scope_and_content': 'scopeAndContent',
        'language_of_material': 'languageOfMaterial',

        # Section 4
        'storage_location': 'storageLocation',
        'rights_statement': 'rightsStatement',
        'rights_statement_type': 'rightsStatementType',
        'rights_statement_value': 'rightsStatementValue',
        'rights_statement_note': 'rightsStatementNote',
        'material_assessment_statement': 'materialAssessmentStatement',
        'appraisal_statement': 'appraisalStatement',
        'associated_documentation': 'associatedDocumentation',

        # Section 5
        'event_statement': 'eventStatement',
        'event_type': 'eventType',
        'event_date': 'eventDate',
        'event_agent': 'eventAgent',

        # Section 6
        'general_notes': 'generalNotes',

        # Section 7
        'rules_or_conventions': 'rulesOrConventions',
        'date_of_creation_or_revision': 'dateOfCreationOrRevision',
        'action_type': 'actionType',
        'action_date': 'actionDate',
        'action_agent': 'actionAgent',
        'action_note': 'actionNote',
    }

    def __init__(self, form_data: dict):
        self.form_data = form_data
        if 'creation_time' in form_data and form_data['creation_time']:
            self.date = form_data['creation_time']
        else:
            self.date = timezone.now().strftime(r'%Y-%m-%d %H:%M:%S')
        self.object = None

    def generate(self):
        self._pre_generation()
        self._generate_section_1()
        self._generate_section_2()
        self._generate_section_3()
        self._generate_section_4()
        self._generate_section_5()
        self._generate_section_6()
        self._generate_section_7()
        self._post_generation()
        return self.object

    def _pre_generation(self):
        pass
    def _pre_section_generation(self, **kwargs):
        pass
    def _post_generation(self):
        pass
    def _post_section_generation(self, **kwargs):
        pass
    def _new_section(self, title):
        pass
    def _new_item_collection(self, title, **kwargs):
        pass

    @abstractmethod
    def _new_item(self, title, data, **kwargs):
        pass

    def _generate_section_1(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=1)
        self._new_section(self.section_titles['section_1'])
        self._new_item(self.item_titles['repository'],
                       DEFAULT_DATA['section_1']['repository'],
                       level=1)
        self._new_item(self.item_titles['accession_identifier'],
                       'Work in Progress!',
                       level=1)

        formset_key = 'formset-otheridentifiers'
        if formset_key in self.form_data and self.form_data[formset_key]:
            valid_forms = [x for x in self.form_data[formset_key] if x]
            num_other_identifiers = len(valid_forms)
            for num, other_id_form in enumerate(valid_forms, 1):
                self._new_item_collection(self.item_titles['other_identifier'],
                                          level=1,
                                          is_array_title=True,
                                          index0=num-1, index1=num, total=num_other_identifiers)
                self._new_item(self.item_titles['other_identifier_type'],
                               other_id_form['other_identifier_type'],
                               level=2,
                               is_array_item=True,
                               index0=num-1, index1=num, total=num_other_identifiers)
                self._new_item(self.item_titles['other_identifier_value'],
                               other_id_form['identifier_value'],
                               level=2,
                               is_array_item=True,
                               index0=num-1, index1=num, total=num_other_identifiers)
                if 'identifier_note' in other_id_form and other_id_form['identifier_note']:
                    self._new_item(self.item_titles['other_identifier_note'],
                                   other_id_form['identifier_note'],
                                   level=2,
                                   is_array_item=True,
                                   index0=num-1, index1=num, total=num_other_identifiers)

        self._new_item(self.item_titles['accession_title'],
                       self.form_data['collection_title'],
                       level=1)
        self._new_item(self.item_titles['archival_unit'],
                       DEFAULT_DATA['section_1']['archival_unit'],
                       level=1)
        self._new_item(self.item_titles['acquisition_method'],
                       DEFAULT_DATA['section_1']['acqusition_method'],
                       level=1)
        self._post_section_generation(section=1)

    def _generate_section_2(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=2)
        self._new_section(self.section_titles['section_2'])
        self._new_item_collection(self.item_titles['source_of_material'],
                                  level=1,
                                  is_array_title=False)
        self._new_item(self.item_titles['source_type'],
                       self.form_data['source_type'],
                       level=2)
        self._new_item(self.item_titles['source_name'],
                       self.form_data['source_name'],
                       level=2)
        self._new_item_collection(self.item_titles['source_contact_information'],
                                  level=2,
                                  is_array_title=False)
        self._new_item(self.item_titles['contact_name'],
                       self.form_data['contact_name'],
                       level=3)
        self._new_item(self.item_titles['job_title'],
                       self.form_data['job_title'],
                       level=3)
        self._new_item(self.item_titles['phone_number'],
                       self.form_data['phone_number'],
                       level=3)
        self._new_item(self.item_titles['email'],
                       self.form_data['email'],
                       level=3)
        self._new_item(self.item_titles['address_line_1'],
                       self.form_data['address_line_1'],
                       level=3)
        self._new_item(self.item_titles['address_line_2'],
                       self.form_data['address_line_2'],
                       level=3)
        self._new_item(self.item_titles['province_or_state'],
                       self.form_data['province_or_state'],
                       level=3)
        self._new_item(self.item_titles['postal_or_zip_code'],
                       self.form_data['postal_or_zip_code'],
                       level=3)
        self._new_item(self.item_titles['country'],
                       self.form_data['country'],
                       level=3)
        self._new_item(self.item_titles['source_role'],
                       self.form_data['source_role'],
                       level=2)
        self._new_item(self.item_titles['source_note'],
                       self.form_data['source_note'],
                       level=2)
        self._new_item(self.item_titles['custodial_history'],
                       self.form_data['custodial_history'],
                       level=1)
        self._post_section_generation(section=2)

    def _generate_section_3(self):
        # TODO: Add checking for non-mandatory fields
        if self.form_data['start_date_is_approximate']:
            start_date = self.approximate_date_format.format(\
            date=self.form_data["start_date_of_material"])
        else:
            start_date = self.form_data['start_date_of_material']
        if self.form_data['end_date_is_approximate']:
            end_date = self.approximate_date_format.format(\
            date=self.form_data["end_date_of_material"])
        else:
            end_date = self.form_data['end_date_of_material']
        date_of_material = f'{start_date} - {end_date}'

        self._pre_section_generation(section=3)
        self._new_section(self.section_titles['section_3'])
        self._new_item(self.item_titles['date_of_material'],
                       date_of_material,
                       level=1)
        self._new_item_collection(self.item_titles['extent_statement'],
                                  level=1)
        self._new_item(self.item_titles['extent_statement_type'],
                       DEFAULT_DATA['section_3']['extent_statement_type'],
                       level=2)
        self._new_item(self.item_titles['quantity_and_type_of_units'],
                       'Work in Progress!!',
                       level=2)
        self._new_item(self.item_titles['extent_statement_note'],
                       DEFAULT_DATA['section_3']['extent_statement_note'],
                       level=2)
        self._new_item(self.item_titles['scope_and_content'],
                       self.form_data['description'],
                       level=1)
        self._new_item(self.item_titles['language_of_material'],
                       self.form_data['language_of_material'],
                       level=1)
        self._post_section_generation(section=3)

    def _generate_section_4(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=4)
        self._new_section(self.section_titles['section_4'])
        if 'storage_location' in self.form_data and self.form_data['storage_location']:
            storage_location = self.form_data['storage_location']
        else:
            storage_location = DEFAULT_DATA['section_4']['storage_location']
        self._new_item(self.item_titles['storage_location'],
                       storage_location,
                       level=1)
        num_rights = 0
        if 'formset-rights' in self.form_data and self.form_data['formset-rights']:
            valid_forms = [x for x in self.form_data['formset-rights'] if x]
            num_rights = len(valid_forms)
            for num, rights_form in enumerate(valid_forms, 1):
                self._new_item_collection(self.item_titles['rights_statement'],
                                          level=1,
                                          is_array_title=True,
                                          index0=num-1, index1=num, total=num_rights)
                self._new_item(self.item_titles['rights_statement_type'],
                               rights_form['rights_type'],
                               level=2,
                               is_array_item=True, index0=num-1, index1=num, total=num_rights)
                self._new_item(self.item_titles['rights_statement_value'],
                               rights_form['rights_statement'],
                               level=2,
                               is_array_item=True, index0=num-1, index1=num, total=num_rights)
                if 'rights_note' in rights_form and rights_form['rights_note']:
                    self._new_item(self.item_titles['rights_statement_note'],
                                   rights_form['rights_note'],
                                   level=2,
                                   is_array_item=True, index0=num-1, index1=num, total=num_rights)
        else:
            LOGGER.warning(msg=('Did not find formset-rights in cleaned form data'))
        if num_rights == 0:
            LOGGER.warning(msg=('Did not find any valid rights forms in formset-rights in cleaned'
                                ' form data'))

        self._new_item(self.item_titles['material_assessment_statement'],
                       DEFAULT_DATA['section_4']['material_assessment_statement'],
                       level=1)
        self._new_item(self.item_titles['appraisal_statement'],
                       DEFAULT_DATA['section_4']['appraisal_statement'],
                       level=1)
        self._new_item(self.item_titles['associated_documentation'],
                       DEFAULT_DATA['section_4']['associated_documentation'],
                       level=1)
        self._post_section_generation(section=4)

    def _generate_section_5(self):
        self._pre_section_generation(section=5)
        self._new_section(self.section_titles['section_5'])
        self._new_item_collection(self.item_titles['event_statement'],
                                  level=1,
                                  is_array_title=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_type'],
                       DEFAULT_DATA['section_5']['event_type'],
                       level=2,
                       is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_date'],
                       self.date,
                       level=2,
                       is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_agent'],
                       DEFAULT_DATA['section_5']['event_agent'],
                       level=2,
                       is_array_item=True, index0=0, index1=1, total=1)
        self._post_section_generation(section=5)

    def _generate_section_6(self):
        self._pre_section_generation(section=6)
        self._new_section(self.section_titles['section_6'])
        if 'general_notes' in self.form_data and self.form_data['general_notes']:
            notes = self.form_data['general_notes']
        else:
            notes = DEFAULT_DATA['section_6']['general_notes']
        self._new_item(self.item_titles['general_notes'],
                       notes,
                       level=1)
        self._post_section_generation(section=6)

    def _generate_section_7(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=7)
        self._new_section(self.section_titles['section_7'])
        self._new_item(self.item_titles['rules_or_conventions'],
                       DEFAULT_DATA['section_7']['rules_or_conventions'],
                       level=1)
        self._new_item_collection(self.item_titles['date_of_creation_or_revision'],
                                  is_array_title=True,
                                  level=1,
                                  index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_type'],
                       DEFAULT_DATA['section_7']['action_type'],
                       is_array_item=True,
                       level=2,
                       index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_date'],
                       self.date,
                       is_array_item=True,
                       level=2,
                       index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_agent'],
                       DEFAULT_DATA['section_7']['action_agent'],
                       is_array_item=True,
                       level=2,
                       index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_note'],
                       DEFAULT_DATA['section_7']['action_note'],
                       is_array_item=True,
                       level=2,
                       index0=0, index1=1, total=1)
        self._post_section_generation(section=7)


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


class BagitTags(ObjectFromForm):
    def __init__(self, form_data: dict):
        super().__init__(form_data)
        self.tags = OrderedDict()

    def _post_generation(self):
        self.object = self.tags

    def _new_item(self, title, data, **kwargs):
        is_array_item = kwargs.get('is_array_item') if 'is_array_item' in kwargs else False
        index1 = kwargs.get('index1') if 'index1' in kwargs else -1

        key = f'{title}_{index1}' if is_array_item else title
        value = data

        self.tags[key] = value
