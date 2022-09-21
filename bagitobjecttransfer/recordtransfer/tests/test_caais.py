import logging
from collections import OrderedDict
from unittest import TestCase

from recordtransfer.caais import convert_transfer_form_to_meta_tree


class TestCaaisMethods(TestCase):

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
            'contact_name': 'James Doe',
            'job_title': 'Legal Secretary',
            'phone_number': '800-222-3333',
            'email': 'j.doe@noreply.org',
            'address_line_1': '123 Any St.',
            'city': 'Anytown',
            'province_or_state': 'Manitoba',
            'postal_or_zip_code': 'H0H0H0',
            'country': 'Canada',
            'source_role': 'Creator',
            'source_type': 'Person',
            'date_of_material': '1980-1990',
            'extent_statement_type': 'Extent received',
            'quantity_and_type_of_units': '1 Document file, totalling 227.18 KiB',
            'extent_statement_note': 'Files counted automatically by application',
            'scope_and_content': 'Various documents',
            'language_of_material': 'English',
            'storage_location': 'Placeholder',
            'formset-rights': [
                {
                    'rights_statement_type': 'Copyright',
                    'rights_statement_value': '',
                    'rights_statement_note': '',
                    'other_rights_statement_type': '',
                },
                {
                    'rights_statement_type': 'Other',
                    'rights_statement_value': 'Until 2035',
                    'rights_statement_note': '',
                    'other_rights_statement_type': 'Intellectual Property',
                }
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
        }
        self.expected_metadata = OrderedDict({
            'section_1': OrderedDict({
                'repository': 'Test Repository',
                'identifiers': [
                    OrderedDict({
                        'identifier_type': 'Accession Identifier',
                        'identifier_value': 'Example identifier',
                        'identifier_note': '',
                    })
                ],
                'accession_title': 'Example title',
                'archival_unit': 'NCTR Archives',
                'acquisition_method': 'Digital Transfer',
                'disposition_authority': '',
            }),
            'section_2': OrderedDict({
                'source_of_information': OrderedDict({
                    'source_type': 'Person',
                    'source_name': 'Jane Doe',
                    'source_contact_information': OrderedDict({
                        'contact_name': 'James Doe',
                        'job_title': 'Legal Secretary',
                        'phone_number': '800-222-3333',
                        'email': 'j.doe@noreply.org',
                        'address_line_1': '123 Any St.',
                        'address_line_2': '',
                        'city': 'Anytown',
                        'province_or_state': 'Manitoba',
                        'postal_or_zip_code': 'H0H0H0',
                        'country': 'Canada',
                    }),
                    'source_role': 'Creator',
                    'source_note': '',
                }),
                'custodial_history': '',
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
                        'rights_statement_type': 'Copyright',
                        'rights_statement_value': '',
                        'rights_statement_note': '',
                        'other_rights_statement_type': '',
                    }),
                    OrderedDict({
                        'rights_statement_type': 'Other',
                        'rights_statement_value': 'Until 2035',
                        'rights_statement_note': '',
                        'other_rights_statement_type': 'Intellectual Property',
                    })
                ],
                'preservation_requirement': [
                    OrderedDict({
                        'preservation_requirement_type': 'Physical Condition',
                        'preservation_requirement_value': 'Record is digital, physical assessment is not possible',
                        'preservation_requirement_note': '',
                    })
                ],
                'appraisal_statement': [],
                'associated_documentation': [],
            }),
            'section_5': OrderedDict({
                'event_statement': [
                    OrderedDict({
                        'event_type': 'Digital Object Transfer',
                        'event_date': '2022-07-04 11:10:33 CDT',
                        'event_agent': 'NCTR Record Transfer Portal',
                        'event_note': '',
                    }),
                ],
            }),
            'section_6': OrderedDict({
                'general_note': '',
            }),
            'section_7': OrderedDict({
                'rules_or_conventions': 'Canadian Archival Accession Information Standards v1.0',
                'level_of_detail': '',
                'date_of_creation_or_revision': [
                    OrderedDict({
                        'action_type': 'Creation',
                        'action_date': '2022-07-04 11:10:33 CDT',
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
        self.expected_metadata['section_4']['preservation_requirement'].append(
            OrderedDict({
                'preservation_requirement_type': 'Contact assessment',
                'preservation_requirement_value': 'Some bumps and bruises',
                'preservation_requirement_note': '',
            }),
        )
        tree = convert_transfer_form_to_meta_tree(self.form_data)
        self.assertDictEqual(self.expected_metadata, tree)
