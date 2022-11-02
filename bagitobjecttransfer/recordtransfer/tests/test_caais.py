import datetime
import logging
from collections import OrderedDict
from django.test import TransactionTestCase

from recordtransfer.caais import convert_transfer_form_to_meta_tree, convert_form_data_to_metadata


class TestCaaisMethods(TransactionTestCase):
    fixtures = ["test_transfer.json"]

    form_data = None

    expected_metadata = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        self.form_data = {
            'repository': 'Test Repository',
            'accession_identifier': 'Example identifier',
            'accession_title': 'Example title',
            'source_name': 'Jane Doe',
            'source_note': 'These are some source notes.',
            'contact_name': 'James Doe',
            'job_title': 'Legal Secretary',
            'phone_number': '800-222-3333',
            'email': 'j.doe@noreply.org',
            'address_line_1': '123 Any Street',
            'address_line_2': 'PO Box 978',
            'city': 'Nashville',
            'province_or_state': 'TN',
            'other_province_or_state': '',
            'postal_or_zip_code': '91111',
            'country': 'US',
            'custodial_history': 'In the past, other people saw this',
            'source_role': 'Creator',
            'source_type': 'Person',
            'date_of_material': '1980-1990',
            'quantity_and_type_of_units': '1 Document file, totalling 227.18 KiB',
            'extent_statement_note': 'Files counted automatically by application',
            'scope_and_content': 'Various documents',
            'language_of_material': 'English',
            'formset-rights': [
                {
                    'rights_statement_type': 'License',
                    'rights_statement_value': '',
                    'rights_statement_note': 'Inherited license from family',
                    'other_rights_statement_type': '',
                },
                {
                    'rights_statement_type': 'Other',
                    'rights_statement_value': 'Until 2035',
                    'rights_statement_note': '',
                    'other_rights_statement_type': 'Intellectual Property',
                }
            ],
            'formset-otheridentifiers': [
                {
                    'identifier_type': 'ARK ID',
                    'identifier_value': 'https://n2t.net/ark:/99999/12345',
                    'identifier_note': 'This is some information about ARK ids.',
                },
            ],
            'material_assessment_statement_type': 'Physical Condition',
            'material_assessment_statement_value': 'Record is digital, physical assessment is not possible',
            'event_type': 'Digital Object Transfer',
            'event_date': '2022-07-04 11:10:33 CDT',
            'event_agent': 'NCTR Record Transfer Portal',
            'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
            'action_type': 'Creation',
            'action_date': '2022-07-04 11:10:33 CDT',
            'action_agent': 'NCTR Record Transfer Portal',
            'language_of_accession_record': 'en',
            'general_note': 'Here is some general note information',
        }
        self.expected_metadata = OrderedDict({
            'section_1': OrderedDict({
                'repository': 'Test Repository',
                'accession_identifier': 'Example identifier',
                'identifiers': [
                    OrderedDict({
                        'identifier_type': 'ARK ID',
                        'identifier_value': 'https://n2t.net/ark:/99999/12345',
                        'identifier_note': 'This is some information about ARK ids.',
                    }),
                ],
                'accession_title': 'Example title',
                'archival_unit': 'NCTR Archives',
                'acquisition_method': 'Digital Transfer',
                'disposition_authority': '',
            }),
            'section_2': OrderedDict({
                'source_type': 'Person',
                'source_name': 'Jane Doe',
                'contact_name': 'James Doe',
                'job_title': 'Legal Secretary',
                'phone_number': '800-222-3333',
                'email_address': 'j.doe@noreply.org',
                'address_line_1': '123 Any Street',
                'address_line_2': 'PO Box 978',
                'city': 'Nashville',
                'region': 'TN',
                'postal_or_zip_code': '91111',
                'country': 'US',
                'source_role': 'Creator',
                'source_note': 'These are some source notes.',
                'custodial_history': 'In the past, other people saw this',
            }),
            'section_3': OrderedDict({
                'date_of_material': '1980-1990',
                'extent_statement': [
                    OrderedDict({
                        'extent_statement_type': 'Extent received',
                        'quantity_and_type_of_units': '1 Document file, totalling 227.18 KiB',
                        'extent_statement_note': 'Files counted automatically by application',
                    })
                ],
                'scope_and_content': 'Various documents',
                'language_of_material': 'English',
            }),
            'section_4': OrderedDict({
                'storage_location': 'Placeholder',
                'rights_statement': [
                    OrderedDict({
                        'rights_statement_type': 'License',
                        'rights_statement_value': '',
                        'rights_statement_note': 'Inherited license from family',
                        'other_rights_statement_type': '',
                    }),
                    OrderedDict({
                        'rights_statement_type': 'Other',
                        'rights_statement_value': 'Until 2035',
                        'rights_statement_note': '',
                        'other_rights_statement_type': 'Intellectual Property',
                    })
                ],
                'material_assessments': [
                    OrderedDict({
                        'material_assessment_statement_type': 'Physical Condition',
                        'material_assessment_statement_value': 'Record is digital, physical assessment is not possible',
                        'material_assessment_statement_plan': '',
                        'material_assessment_statement_note': '',
                    })
                ],
                'appraisal_statement': [],
                'associated_documentation': [],
            }),
            'section_5': OrderedDict({
                'event_statement': [
                    OrderedDict({
                        'event_type': 'Digital Object Transfer',
                        'event_agent': 'NCTR Record Transfer Portal',
                        'event_note': '',
                    }),
                ],
            }),
            'section_6': OrderedDict({
                'general_note': 'Here is some general note information',
            }),
            'section_7': OrderedDict({
                'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
                'level_of_detail': '',
                'date_of_creation_or_revision': [
                    OrderedDict({
                        'action_type': 'Creation',
                        'action_agent': 'NCTR Record Transfer Portal',
                        'action_note': '',
                    }),
                ],
                'language_of_accession_record': 'en',
            }),
        })

    def test_translate_basic_form_data(self):
        """ Test the translation of basic form data to caais structure. """
        tree = convert_transfer_form_to_meta_tree(self.form_data)
        self.assertDictEqual(self.expected_metadata, tree)

    def test_translate_form_data_condition_assessment(self):
        """ Add in a condition assessment. """
        self.form_data['condition_assessment'] = "Some bumps and bruises"
        self.expected_metadata['section_4']['material_assessments'].append(
            OrderedDict({
                'material_assessment_statement_type': 'Contact assessment',
                'material_assessment_statement_value': 'Some bumps and bruises',
            }),
        )
        tree = convert_transfer_form_to_meta_tree(self.form_data)
        self.assertDictEqual(self.expected_metadata, tree)

    def test_form_data_to_models(self):
        # Remove some defaults that are needed for the above tests, but not here.
        del self.form_data['accession_identifier']
        del self.form_data['material_assessment_statement_type']
        del self.form_data['material_assessment_statement_value']
        del self.form_data['event_type']
        del self.form_data['event_agent']
        del self.form_data['event_date']
        del self.form_data['rules_or_conventions']
        del self.form_data['language_of_accession_record']
        del self.form_data['action_type']
        del self.form_data['action_agent']
        del self.form_data['action_date']
        # Add in a contact assessment.
        self.expected_metadata['section_4']['material_assessments'].append(
            OrderedDict({
                'material_assessment_statement_type': 'Contact assessment',
                'material_assessment_statement_value': 'Some bumps and bruises',
            }),
        )
        start_time = datetime.datetime.now()
        metadata = convert_form_data_to_metadata(self.form_data)
        self.assertEqual(self.form_data['accession_title'], metadata.accession_title)
        self.assertEqual('Not assigned', metadata.accession_identifier)
        self.assertEqual('en', metadata.language_of_record)
        self.assertEqual(self.form_data['scope_and_content'], metadata.scope_and_content)
        self.assertEqual(self.form_data['custodial_history'], metadata.custodial_history)
        self.assertEqual(self.form_data['date_of_material'], metadata.date_of_material)
        self.assertEqual('Canadian Archival Accession Information Standards v1.0', metadata.rules_or_conventions)
        self.assertEqual('', metadata.level_of_detail)
        self.assertEqual(self.form_data['repository'], metadata.repository)

        self.assertEqual(1, metadata.source_of_materials.count())
        source_of_material = metadata.source_of_materials.first()
        self.assertEqual(self.form_data['source_name'], source_of_material.source_name)
        self.assertEqual(self.form_data['source_type'], source_of_material.source_type.name)
        self.assertEqual(self.form_data['source_role'], source_of_material.source_role.name)
        self.assertEqual(self.form_data['contact_name'], source_of_material.contact_name)
        self.assertEqual(self.form_data['job_title'], source_of_material.job_title)
        self.assertEqual(self.form_data['phone_number'], source_of_material.phone_number)
        self.assertEqual(self.form_data['email'], source_of_material.email_address)
        self.assertEqual(self.form_data['address_line_1'], source_of_material.address_line_1)
        self.assertEqual(self.form_data['address_line_2'], source_of_material.address_line_2)
        self.assertEqual(self.form_data['city'], source_of_material.city)
        prov_state = self.form_data['province_or_state']
        if prov_state.lower() == 'other':
            prov_state = self.form_data['other_province_or_state']
        self.assertEqual(prov_state, source_of_material.region)
        self.assertEqual(self.form_data['postal_or_zip_code'], source_of_material.postal_or_zip_code)
        self.assertEqual(self.form_data['country'], source_of_material.country)
        self.assertEqual(self.form_data['source_note'], source_of_material.source_note)

        self.assertEqual(1, metadata.extent_statements.count())
        extent = metadata.extent_statements.first()
        self.assertEqual('Extent received', extent.extent_type.name)  # Default
        self.assertEqual(self.form_data['quantity_and_type_of_units'], extent.quantity_and_type_of_units)
        self.assertEqual('Files counted automatically by application', extent.extent_note)  # Default

        self.assertEqual(1, metadata.language_of_materials.count())
        languages = metadata.language_of_materials.first()
        self.assertEqual(self.form_data['language_of_material'], languages.language_of_material)

        self.assertEqual(1, metadata.storage_locations.count())
        storage_location = metadata.storage_locations.first()
        self.assertEqual('Placeholder', storage_location.storage_location)  # Default

        counter = 0
        for right in metadata.rights.all():
            if self.form_data['formset-rights'][counter]['rights_statement_type'].lower() == 'other':
                self.assertEqual(
                    self.form_data['formset-rights'][counter]['other_rights_statement_type'],
                    right.rights_type.name
                )
            else:
                self.assertEqual(
                    self.form_data['formset-rights'][counter]['rights_statement_type'],
                    right.rights_type.name
                )
            self.assertEqual(
                self.form_data['formset-rights'][counter]['rights_statement_value'],
                right.rights_value
            )
            self.assertEqual(
                self.form_data['formset-rights'][counter]['rights_statement_note'],
                right.rights_note
            )
            counter += 1

        counter = 0
        for assessment in metadata.material_assessments.all():
            if counter == 0:
                self.assertEqual('Physical Condition', assessment.assessment_type.name)
                self.assertEqual('Record is digital, physical assessment is not possible', assessment.assessment_value)
            elif counter == 1:
                self.assertEqual('Contact assessment', assessment.assessment_type.name)
                self.assertEqual('Some bumps and bruises', assessment.assessment_value)

        self.assertEqual(1, metadata.events.count())
        event = metadata.events.first()
        self.assertEqual('Digital Object Transfer', event.event_type.name)
        self.assertEqual('NCTR Record Transfer Portal', event.event_agent)
        self.assertAlmostEqual(start_time.timestamp(), event.event_date.timestamp(), 1)

        self.assertEqual(1, metadata.date_creation_revisions.count())
        creation_revision_date = metadata.date_creation_revisions.first()
        self.assertEqual('Creation', creation_revision_date.action_type.name)
        self.assertEqual('NCTR Record Transfer Portal', creation_revision_date.action_agent)
        self.assertAlmostEqual(start_time.timestamp(), creation_revision_date.action_date.timestamp(), 1)

        self.assertEqual(1, metadata.general_notes.count())
        note = metadata.general_notes.first()
        self.assertEqual(self.form_data['general_note'], note.note)

        self.assertEqual(1, metadata.archival_units.count())
        archival_unit = metadata.archival_units.first()
        self.assertEqual('NCTR Archives', archival_unit.archival_unit)
