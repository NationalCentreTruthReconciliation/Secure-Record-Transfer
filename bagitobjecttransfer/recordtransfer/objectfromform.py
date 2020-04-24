from abc import ABC, abstractmethod

from recordtransfer.defaultdata import DEFAULT_DATA

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
            from datetime import datetime
            self.date = datetime.strftime(datetime.today(), r'%Y-%m-%d %H:%M:%S')
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

    def _pre_generation(self): pass
    def _pre_section_generation(self, **kwargs): pass
    def _post_generation(self): pass
    def _post_section_generation(self, **kwargs): pass
    def _new_section(self, title): pass
    def _new_item_collection(self, title, **kwargs): pass

    @abstractmethod
    def _new_item(self, title, data, **kwargs): pass

    def _generate_section_1(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=1)
        self._new_section(self.section_titles['section_1'])
        self._new_item(self.item_titles['repository'], DEFAULT_DATA['section_1']['repository'], level=1)
        self._new_item(self.item_titles['accession_identifier'], 'Work in Progress!', level=1)

        if 'formset-otheridentifiers' in self.form_data and self.form_data['formset-otheridentifiers']:
            empty_forms_filtered = list(filter(None, self.form_data['formset-otheridentifiers']))
            num_other_identifiers = len(empty_forms_filtered)
            for num, other_id_form in enumerate(empty_forms_filtered, start=1):
                self._new_item_collection(self.item_titles['other_identifier'], level=1, is_array_title=True,
                    index0=num-1, index1=num, total=num_other_identifiers)
                self._new_item(self.item_titles['other_identifier_type'], other_id_form['other_identifier_type'],
                    level=2, is_array_item=True, index0=num-1, index1=num, total=num_other_identifiers)
                self._new_item(self.item_titles['other_identifier_value'], other_id_form['identifier_value'],
                    level=2, is_array_item=True, index0=num-1, index1=num, total=num_other_identifiers)
                if 'identifier_note' in other_id_form and other_id_form['identifier_note']:
                    self._new_item(self.item_titles['other_identifier_note'], other_id_form['identifier_note'],
                        level=2, is_array_item=True, index0=num-1, index1=num, total=num_other_identifiers)

        self._new_item(self.item_titles['accession_title'], self.form_data['collection_title'], level=1)
        self._new_item(self.item_titles['archival_unit'], DEFAULT_DATA['section_1']['archival_unit'], level=1)
        self._new_item(self.item_titles['acquisition_method'], DEFAULT_DATA['section_1']['acqusition_method'], level=1)
        self._post_section_generation(section=1)

    def _generate_section_2(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=2)
        self._new_section(self.section_titles['section_2'])
        self._new_item_collection(self.item_titles['source_of_material'], level=1, is_array_title=False)
        self._new_item(self.item_titles['source_type'], self.form_data['source_type'], level=2)
        self._new_item(self.item_titles['source_name'], self.form_data['source_name'], level=2)
        self._new_item_collection(self.item_titles['source_contact_information'], level=2, is_array_title=False)
        self._new_item(self.item_titles['contact_name'], self.form_data['contact_name'], level=3)
        self._new_item(self.item_titles['job_title'], self.form_data['job_title'], level=3)
        self._new_item(self.item_titles['phone_number'], self.form_data['phone_number'], level=3)
        self._new_item(self.item_titles['email'], self.form_data['email'], level=3)
        self._new_item(self.item_titles['address_line_1'], self.form_data['address_line_1'], level=3)
        self._new_item(self.item_titles['address_line_2'], self.form_data['address_line_2'], level=3)
        self._new_item(self.item_titles['province_or_state'], self.form_data['province_or_state'], level=3)
        self._new_item(self.item_titles['postal_or_zip_code'], self.form_data['postal_or_zip_code'], level=3)
        self._new_item(self.item_titles['country'], self.form_data['country'], level=3)
        self._new_item(self.item_titles['source_role'], self.form_data['source_role'], level=2)
        self._new_item(self.item_titles['source_note'], self.form_data['source_note'], level=2)
        self._new_item(self.item_titles['custodial_history'], self.form_data['custodial_history'], level=1)
        self._post_section_generation(section=2)

    def _generate_section_3(self):
        # TODO: Add checking for non-mandatory fields
        if self.form_data['start_date_is_approximate']:
            start_date = self.approximate_date_format.format(date=self.form_data["start_date_of_material"])
        else:
            start_date = self.form_data['start_date_of_material']
        if self.form_data['end_date_is_approximate']:
            end_date = self.approximate_date_format.format(date=self.form_data["end_date_of_material"])
        else:
            end_date = self.form_data['end_date_of_material']
        date_of_material = f'{start_date} - {end_date}'

        self._pre_section_generation(section=3)
        self._new_section(self.section_titles['section_3'])
        self._new_item(self.item_titles['date_of_material'], date_of_material, level=1)
        self._new_item_collection(self.item_titles['extent_statement'], level=1)
        self._new_item(self.item_titles['extent_statement_type'], DEFAULT_DATA['section_3']['extent_statement_type'],
            level=2)
        self._new_item(self.item_titles['quantity_and_type_of_units'], 'Work in Progress!!', level=2)
        self._new_item(self.item_titles['extent_statement_note'], DEFAULT_DATA['section_3']['extent_statement_note'],
            level=2)
        self._new_item(self.item_titles['scope_and_content'], self.form_data['description'], level=1)
        self._new_item(self.item_titles['language_of_material'], self.form_data['language_of_material'], level=1)
        self._post_section_generation(section=3)

    def _generate_section_4(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=4)
        self._new_section(self.section_titles['section_4'])
        storage_location = self.form_data['storage_location'] if 'storage_location' in self.form_data \
            else DEFAULT_DATA['section_4']['storage_location']
        self._new_item(self.item_titles['storage_location'], storage_location, level=1)

        num_rights = 0
        if 'formset-rights' in self.form_data and self.form_data['formset-rights']:
            empty_forms_filtered = list(filter(None, self.form_data['formset-rights']))
            num_rights = len(empty_forms_filtered)
            for num, rights_form in enumerate(empty_forms_filtered, start=1):
                self._new_item_collection(self.item_titles['rights_statement'], level=1, is_array_title=True,
                    index0=num-1, index1=num, total=num_rights)
                self._new_item(self.item_titles['rights_statement_type'], rights_form['rights_type'], level=2,
                    is_array_item=True, index0=num-1, index1=num, total=num_rights)
                self._new_item(self.item_titles['rights_statement_value'], rights_form['rights_statement'], level=2,
                    is_array_item=True, index0=num-1, index1=num, total=num_rights)
                if 'rights_note' in rights_form and rights_form['rights_note']:
                    self._new_item(self.item_titles['rights_statement_note'], rights_form['rights_note'], level=2,
                        is_array_item=True, index0=num-1, index1=num, total=num_rights)
        else:
            LOGGER.warn(msg=('Did not find formset-rights in cleaned form data'))
        if num_rights == 0:
            LOGGER.warn(msg=('Did not find any valid rights forms in formset-rights in cleaned form data'))

        self._new_item(self.item_titles['material_assessment_statement'],
            DEFAULT_DATA['section_4']['material_assessment_statement'], level=1)
        self._new_item(self.item_titles['appraisal_statement'],
            DEFAULT_DATA['section_4']['appraisal_statement'], level=1)
        self._new_item(self.item_titles['associated_documentation'],
            DEFAULT_DATA['section_4']['associated_documentation'], level=1)
        self._post_section_generation(section=4)

    def _generate_section_5(self):
        self._pre_section_generation(section=5)
        self._new_section(self.section_titles['section_5'])
        self._new_item_collection(self.item_titles['event_statement'], level=1,
            is_array_title=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_type'], DEFAULT_DATA['section_5']['event_type'], level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_date'], self.date, leve1=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['event_agent'], DEFAULT_DATA['section_5']['event_agent'], level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._post_section_generation(section=5)

    def _generate_section_6(self):
        self._pre_section_generation(section=6)
        self._new_section(self.section_titles['section_6'])
        if 'general_notes' in self.form_data and self.form_data['general_notes']:
            self._new_item(self.item_titles['general_notes'], self.form_data['general_notes'], level=1)
        else:
            self._new_item(self.item_titles['general_notes'], DEFAULT_DATA['section_6']['general_notes'], level=1)
        self._post_section_generation(section=6)

    def _generate_section_7(self):
        # TODO: Add checking for non-mandatory fields
        self._pre_section_generation(section=7)
        self._new_section(self.section_titles['section_7'])
        self._new_item(self.item_titles['rules_or_conventions'], DEFAULT_DATA['section_7']['rules_or_conventions'],
            level=1)
        self._new_item_collection(self.item_titles['date_of_creation_or_revision'], level=1,
            is_array_title=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_type'], DEFAULT_DATA['section_7']['action_type'], level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_date'], self.date, level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_agent'], DEFAULT_DATA['section_7']['action_agent'], level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._new_item(self.item_titles['action_note'], DEFAULT_DATA['section_7']['action_note'], level=2,
            is_array_item=True, index0=0, index1=1, total=1)
        self._post_section_generation(section=7)
