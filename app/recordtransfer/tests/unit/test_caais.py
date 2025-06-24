from datetime import datetime
from unittest.mock import patch
import logging

from django.test import TestCase
from django.utils import timezone

from caais.models import *
from recordtransfer.caais import (
    map_form_to_metadata,
    add_identifiers,
    add_source_of_materials,
    add_rights,
    add_submission_event,
    add_date_of_creation,
    add_related_models,
)

@patch('recordtransfer.caais.add_identifiers')
@patch('recordtransfer.caais.add_source_of_materials')
@patch('recordtransfer.caais.add_rights')
@patch('recordtransfer.caais.add_submission_event')
@patch('recordtransfer.caais.add_date_of_creation')
@patch('recordtransfer.caais.add_related_models')
class TestFormToMetadata(TestCase):
    ''' Test the conversion from the metadata form to a caais.models.Metadata
    object.

    NOTE: All related objects are ignored for this test case, hence all the
    patches on this class.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @patch('django.conf.settings.CAAIS_DEFAULT_REPOSITORY', '')
    def test_populate_repository_no_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.repository, '')

    @patch('django.conf.settings.CAAIS_DEFAULT_REPOSITORY', 'REPOSITORY A')
    def test_populate_repository_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.repository, 'REPOSITORY A')

    @patch('django.conf.settings.CAAIS_DEFAULT_ACCESSION_TITLE', '')
    def test_populate_accession_title_no_default(self, *patches):
        form_data = {
            'accession_title': 'My Title',
        }

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.accession_title, 'My Title')

    @patch('django.conf.settings.CAAIS_DEFAULT_ACCESSION_TITLE', 'TITLE A')
    def test_populate_accession_title_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.accession_title, 'TITLE A')

    @patch('django.conf.settings.CAAIS_DEFAULT_ACCESSION_TITLE', 'TITLE A')
    def test_populate_accession_title_with_default_prefer_form(self, *patches):
        form_data = {
            'accession_title': 'My Title',
        }

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.accession_title, 'My Title')

    @patch('django.conf.settings.CAAIS_DEFAULT_ACQUISITION_METHOD', '')
    def test_populate_acquisition_method_no_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertFalse(metadata.acquisition_method)

    @patch('django.conf.settings.CAAIS_DEFAULT_ACQUISITION_METHOD', 'Digital Transfer')
    def test_populate_acquisition_method_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertTrue(metadata.acquisition_method)
        self.assertEqual(metadata.acquisition_method.name, 'Digital Transfer')

    @patch('django.conf.settings.CAAIS_DEFAULT_ACQUISITION_METHOD', 'Digital Transfer 2')
    def test_populate_acquisition_method_with_default_already_created(self, *patches):
        term, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer 2')
        self.assertTrue(term) # Verify that it exists

        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertTrue(metadata.acquisition_method)
        self.assertEqual(metadata.acquisition_method.name, 'Digital Transfer 2')

    @patch('django.conf.settings.CAAIS_DEFAULT_STATUS', '')
    def test_populate_status_no_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertFalse(metadata.status)

    @patch('django.conf.settings.CAAIS_DEFAULT_STATUS', 'Not Reviewed')
    def test_populate_status_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertTrue(metadata.status)
        self.assertEqual(metadata.status.name, 'Not Reviewed')

    @patch('django.conf.settings.CAAIS_DEFAULT_STATUS', 'Transferred, Not Reviewed')
    def test_populate_status_with_default_already_created(self, *patches):
        term, _ = Status.objects.get_or_create(name='Transferred, Not Reviewed')
        self.assertTrue(term) # Verify it exists

        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertTrue(metadata.status)
        self.assertEqual(metadata.status.name, 'Transferred, Not Reviewed')

    @patch('django.conf.settings.CAAIS_DEFAULT_DATE_OF_MATERIALS', '')
    def test_populate_date_of_materials_no_default(self, *patches):
        form_data = {
            'date_of_materials': '2010',
        }

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.date_of_materials, '2010')

    @patch('django.conf.settings.CAAIS_DEFAULT_DATE_OF_MATERIALS', '2016-01-01 - 2018-12-31')
    def test_populate_date_of_materials_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.date_of_materials, '2016-01-01 - 2018-12-31')

    @patch('django.conf.settings.CAAIS_DEFAULT_DATE_OF_MATERIALS', '2018')
    def test_populate_date_of_materials_with_default_prefer_form(self, *patches):
        form_data = {
            'date_of_materials': '2001'
        }

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.date_of_materials, '2001')

    @patch('django.conf.settings.CAAIS_DEFAULT_RULES_OR_CONVENTIONS', '')
    def test_populate_rules_or_conventions_no_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.rules_or_conventions, '')

    @patch('django.conf.settings.CAAIS_DEFAULT_RULES_OR_CONVENTIONS', 'CAAIS v1.0')
    def test_populate_rules_or_conventions_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.rules_or_conventions, 'CAAIS v1.0')

    @patch('django.conf.settings.CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD', '')
    def test_populate_language_of_accession_record_no_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.language_of_accession_record, '')

    @patch('django.conf.settings.CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD', 'English')
    def test_populate_language_of_accession_record_with_default(self, *patches):
        form_data = {}

        metadata = map_form_to_metadata(form_data)

        self.assertEqual(metadata.language_of_accession_record, 'English')


class TestFormToIdentifiers(TestCase):
    ''' Test the conversion from the metadata form to caais.models.Identifier
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    def test_no_identifiers(self):
        form_data = {}

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 0)

    def test_no_identifiers_empty_list(self):
        ''' Test an empty set of identifiers. The key exist, but the list is
        empty.
        '''
        form_data = {
            'formset-otheridentifiers': []
        }

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 0)

    def test_no_identifiers_empty_data(self):
        ''' Test various "empty" identifiers that should not yield an identifier.
        '''
        form_data = {
            'formset-otheridentifiers': [
                None,
                {},
                {
                    'other_identifier_type': '',
                    'other_identifier_value': '',
                    'other_identifier_note': '',
                },
            ]
        }

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 0)

    def test_populate_one_identifier(self):
        form_data = {
            'formset-otheridentifiers': [
                {
                    'other_identifier_type': 'ID Type',
                    'other_identifier_value': '123-000-111',
                    'other_identifier_note': 'My note',
                },
            ]
        }

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 1)

        identifier = self.metadata.identifiers.first()
        self.assertEqual(identifier.identifier_type, 'ID Type')
        self.assertEqual(identifier.identifier_value, '123-000-111')
        self.assertEqual(identifier.identifier_note, 'My note')

    def test_populate_multiple_identifiers(self):
        form_data = {
            'formset-otheridentifiers': [
                {
                    'other_identifier_type': 'ID Type 1',
                    'other_identifier_value': '123-000-111',
                    'other_identifier_note': 'My note',
                },
                {
                    'other_identifier_type': 'ID Type 2',
                    'other_identifier_value': '888111',
                    'other_identifier_note': '',
                },
                {
                    'other_identifier_type': '',
                    'other_identifier_value': '999000',
                    'other_identifier_note': '',
                },
            ]
        }

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 3)

        id_1, id_2, id_3 = self.metadata.identifiers.all()

        self.assertEqual(id_1.identifier_type, 'ID Type 1')
        self.assertEqual(id_1.identifier_value, '123-000-111')
        self.assertEqual(id_1.identifier_note, 'My note')

        self.assertEqual(id_2.identifier_type, 'ID Type 2')
        self.assertEqual(id_2.identifier_value, '888111')
        self.assertEqual(id_2.identifier_note, '')

        self.assertEqual(id_3.identifier_type, '')
        self.assertEqual(id_3.identifier_value, '999000')
        self.assertEqual(id_3.identifier_note, '')

    def test_populate_identifier_ignore_duplicates(self):
        form_data = {
            'formset-otheridentifiers': [
                {
                    'other_identifier_type': 'ID Type 1',
                    'other_identifier_value': '123-000-111',
                    'other_identifier_note': 'My note',
                },
                {
                    'other_identifier_type': 'ID Type 1',
                    'other_identifier_note': 'My note',
                    'other_identifier_value': '123-000-111',
                },
                {
                    'other_identifier_type': 'ID Type 1',
                    'other_identifier_note': 'My note',
                    'other_identifier_value': '123-000-111',
                },
            ]
        }

        add_identifiers(form_data, self.metadata)

        self.assertEqual(self.metadata.identifiers.count(), 1)


class TestFormToArchivalUnit(TestCase):
    ''' Test the conversion from the metadata form to caais.models.ArchivalUnit
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_ARCHIVAL_UNIT', '')
    def test_populate_archival_unit_no_default(self):
        add_related_models({}, self.metadata, ArchivalUnit)

        self.assertEqual(self.metadata.archival_units.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_ARCHIVAL_UNIT', 'Archives Unit')
    def test_populate_archival_unit_with_default(self):
        add_related_models({}, self.metadata, ArchivalUnit)

        self.assertEqual(self.metadata.archival_units.count(), 1)
        self.assertEqual(self.metadata.archival_units.first().archival_unit, 'Archives Unit')


class TestFormToDispositionAuthority(TestCase):
    ''' Test the conversion from the metadata form to caais.models.DispositionAuthority
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_DISPOSITION_AUTHORITY', '')
    def test_populate_disposition_authority_no_default(self):
        add_related_models({}, self.metadata, DispositionAuthority)

        self.assertEqual(self.metadata.disposition_authorities.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_DISPOSITION_AUTHORITY', 'Disposition Authority')
    def test_populate_disposition_authority_with_default(self):
        add_related_models({}, self.metadata, DispositionAuthority)

        self.assertEqual(self.metadata.disposition_authorities.count(), 1)
        self.assertEqual(
            self.metadata.disposition_authorities.first().disposition_authority,
            'Disposition Authority'
        )


class TestFormToSourceOfMaterial(TestCase):
    ''' Test the conversion from the metadata form to caais.models.SourceOfMaterial
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()
        self.other_source_role, _ = SourceRole.objects.get_or_create(name='Other')
        self.other_source_type, _ = SourceType.objects.get_or_create(name='Other')


    @patch('django.conf.settings.CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY', '')
    def test_populate_source_of_material_no_data(self):
        form_data = {}

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY', 'Anonymous')
    def test_populate_source_of_materials_with_default_confidentiality(self):
        form_data = {}

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        self.assertTrue(self.metadata.source_of_materials.first().source_confidentiality)
        self.assertEqual(
            self.metadata.source_of_materials.first().source_confidentiality.name,
            'Anonymous'
        )

    @patch('django.conf.settings.CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY', '')
    def test_add_source_of_material_no_other_types_chosen(self):
        ''' Add source of material, where no "Other" types were chosen '''
        source_type, _ = SourceType.objects.get_or_create(name='Individual')
        source_role, _ = SourceRole.objects.get_or_create(name='Custodian')

        form_data = {
            'source_type': source_type,
            'source_role': source_role,
            'source_note': 'Notes notes notes.',
            'source_name': 'Person',
            'contact_name': 'Contact person',
            'job_title': 'Job',
            'organization': 'Org',
            'phone_number': '999 111-0000',
            'email': 'user@example.com',
            'address_line_1': '100 4th Street',
            'address_line_2': 'Apt 10',
            'city': 'Winnipeg',
            'province_or_state': 'MB',
            'postal_or_zip_code': 'R5R 5R5',
            'country': 'CA',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertTrue(source.source_type)
        self.assertEqual(source.source_type.name, 'Individual')
        self.assertEqual(source.source_name, 'Person')
        self.assertEqual(source.contact_name, 'Contact person')
        self.assertEqual(source.job_title, 'Job')
        self.assertEqual(source.organization, 'Org')
        self.assertEqual(source.phone_number, '999 111-0000')
        self.assertEqual(source.email_address, 'user@example.com')
        self.assertEqual(source.address_line_1, '100 4th Street')
        self.assertEqual(source.address_line_2, 'Apt 10')
        self.assertEqual(source.city, 'Winnipeg')
        self.assertEqual(source.region, 'MB')
        self.assertEqual(source.postal_or_zip_code, 'R5R 5R5')
        self.assertEqual(source.country, 'CA')
        self.assertTrue(source.source_role)
        self.assertEqual(source.source_role.name, 'Custodian')
        self.assertEqual(source.source_note, 'Notes notes notes.')
        self.assertFalse(source.source_confidentiality)


    def test_populate_source_of_material_other_source_type(self):
        form_data = {
            'source_type': self.other_source_type,
            'other_source_type': 'Committee',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_type, self.other_source_type)
        self.assertEqual(source.source_note, "Source type was noted as 'Committee'")

    def test_populate_source_of_materials_other_source_type_with_note(self):
        form_data = {
            'source_type': self.other_source_type,
            'other_source_type': 'Organization',
            'source_note': 'Test test test',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_type, self.other_source_type)
        self.assertEqual(
            source.source_note,
            "Source type was noted as 'Organization'. Test test test"
        )

    def test_populate_source_of_materials_prefer_source_type_over_other(self):
        source_type, created = SourceType.objects.get_or_create(name='Person')

        form_data = {
            'source_type': source_type,
            'other_source_type': 'Individual',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_type, source_type)
        self.assertEqual(source.source_note, '')

        if created:
            source_type.delete()

    def test_populate_source_of_material_other_source_role(self):
        form_data = {
            'source_role': self.other_source_role,
            'other_source_role': 'Data steward',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_role, self.other_source_role)
        self.assertEqual(source.source_note, "Source role was noted as 'Data steward'")

    def test_populate_source_of_materials_other_source_role_with_note(self):
        form_data = {
            'source_role': self.other_source_role,
            'other_source_role': 'Data custodian',
            'source_note': 'Test test test',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_role, self.other_source_role)
        self.assertEqual(
            source.source_note,
            "Source role was noted as 'Data custodian'. Test test test"
        )

    def test_populate_source_of_materials_prefer_source_role_over_other(self):
        source_role, created = SourceRole.objects.get_or_create(name='Custodian')

        form_data = {
            'source_role': source_role,
            'other_source_role': 'Data custodian',
        }

        add_source_of_materials(form_data, self.metadata)

        self.assertEqual(self.metadata.source_of_materials.count(), 1)
        source = self.metadata.source_of_materials.first()
        self.assertEqual(source.source_role, source_role)
        self.assertEqual(source.source_note, '')

        if created:
            source_role.delete()


class TestFormToPreliminaryCustodialHistory(TestCase):
    ''' Test the conversion from the metadata form to caais.models.PreliminaryCustodialHistory
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY', '')
    def test_populate_prelim_custodial_history_no_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, PreliminaryCustodialHistory)

        self.assertEqual(self.metadata.preliminary_custodial_histories.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY', 'No history recorded.')
    def test_populate_prelim_custodial_history_with_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, PreliminaryCustodialHistory)

        self.assertEqual(self.metadata.preliminary_custodial_histories.count(), 1)
        self.assertEqual(
            self.metadata.preliminary_custodial_histories.first().preliminary_custodial_history,
            'No history recorded.'
        )

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY', 'No history recorded.')
    def test_populate_prelim_custodial_history_with_default_prefer_form(self):
        form_data = {
            'preliminary_custodial_history': 'History of custody.'
        }

        add_related_models(form_data, self.metadata, PreliminaryCustodialHistory)

        self.assertEqual(self.metadata.preliminary_custodial_histories.count(), 1)
        self.assertEqual(
            self.metadata.preliminary_custodial_histories.first().preliminary_custodial_history,
            'History of custody.'
        )


class TestFormToExtentStatment(TestCase):
    ''' Test the conversion from the metadata form to caais.models.ExtentStatement
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CONTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CARRIER_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_NOTE', '')
    def test_populate_extent_no_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, ExtentStatement)

        self.assertEqual(self.metadata.extent_statements.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_TYPE', 'Extent Received')
    @patch('django.conf.settings.CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE', 'No files transferred.')
    @patch('django.conf.settings.CAAIS_DEFAULT_CONTENT_TYPE', 'Metadata-Only Transfer')
    @patch('django.conf.settings.CAAIS_DEFAULT_CARRIER_TYPE', 'Digital Transfer')
    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_NOTE', 'File uploads are disabled.')
    def test_populate_all_defaults(self):
        form_data = {}

        add_related_models(form_data, self.metadata, ExtentStatement)

        extent = self.metadata.extent_statements.first()

        self.assertTrue(extent.extent_type)
        self.assertEqual(extent.extent_type.name, 'Extent Received')
        self.assertEqual(extent.quantity_and_unit_of_measure, 'No files transferred.')
        self.assertTrue(extent.content_type)
        self.assertEqual(extent.content_type.name, 'Metadata-Only Transfer')
        self.assertTrue(extent.carrier_type)
        self.assertEqual(extent.carrier_type.name, 'Digital Transfer')
        self.assertEqual(extent.extent_note, 'File uploads are disabled.')

    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CONTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CARRIER_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_NOTE', '')
    def test_populate_extent_from_form_no_defaults(self):
        form_data = {
            'quantity_and_unit_of_measure': '12 PDF files',
        }

        add_related_models(form_data, self.metadata, ExtentStatement)

        extent = self.metadata.extent_statements.first()

        self.assertFalse(extent.extent_type)
        self.assertEqual(extent.quantity_and_unit_of_measure, '12 PDF files')
        self.assertFalse(extent.content_type)
        self.assertFalse(extent.extent_note)
        self.assertFalse(extent.carrier_type)

    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE', 'No quantity or unit of measure.')
    @patch('django.conf.settings.CAAIS_DEFAULT_CONTENT_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CARRIER_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_EXTENT_NOTE', '')
    def test_populate_extent_with_default_prefer_form(self):
        form_data = {
            'quantity_and_unit_of_measure': '3 excel spreadsheets',
        }

        add_related_models(form_data, self.metadata, ExtentStatement)

        extent = self.metadata.extent_statements.first()

        self.assertEqual(extent.quantity_and_unit_of_measure, '3 excel spreadsheets')


class TestFormToPreliminaryScopeAndContent(TestCase):
    ''' Test the conversion from the metadata form to caais.models.PreliminaryScopeAndContent
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT', '')
    def test_populate_prelim_scope_and_content_no_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, PreliminaryScopeAndContent)

        self.assertEqual(self.metadata.preliminary_custodial_histories.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT', 'No scope and content provided.')
    def test_populate_prelim_scope_and_content_with_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, PreliminaryScopeAndContent)

        self.assertEqual(self.metadata.preliminary_scope_and_contents.count(), 1)
        self.assertEqual(
            self.metadata.preliminary_scope_and_contents.first().preliminary_scope_and_content,
            'No scope and content provided.'
        )

    @patch('django.conf.settings.CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT', 'No scope and content recorded.')
    def test_populate_prelim_scope_and_content_with_default_prefer_form(self):
        form_data = {
            'preliminary_scope_and_content': 'Provided scope and content'
        }

        add_related_models(form_data, self.metadata, PreliminaryScopeAndContent)

        self.assertEqual(self.metadata.preliminary_scope_and_contents.count(), 1)
        self.assertEqual(
            self.metadata.preliminary_scope_and_contents.first().preliminary_scope_and_content,
            'Provided scope and content'
        )


class TestFormToLanguageOfMaterial(TestCase):
    ''' Test the conversion from the metadata form to caais.models.LanguageOfMaterial
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL', '')
    def test_populate_language_of_material_no_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, LanguageOfMaterial)

        self.assertEqual(self.metadata.language_of_materials.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL', 'EN')
    def test_populate_language_of_material_with_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, LanguageOfMaterial)

        self.assertEqual(self.metadata.language_of_materials.count(), 1)
        self.assertEqual(self.metadata.language_of_materials.first().language_of_material, 'EN')

    @patch('django.conf.settings.CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL', 'EN')
    def test_populate_language_of_material_with_default_prefer_form(self):
        form_data = {
            'language_of_material': 'French'
        }

        add_related_models(form_data, self.metadata, LanguageOfMaterial)

        self.assertEqual(self.metadata.language_of_materials.count(), 1)
        self.assertEqual(self.metadata.language_of_materials.first().language_of_material, 'French')


class TestFormToStorageLocation(TestCase):
    ''' Test the conversion from the metadata form to caais.models.StorageLocation
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_STORAGE_LOCATION', '')
    def test_populate_storage_location_no_default(self):
        add_related_models({}, self.metadata, StorageLocation)

        self.assertEqual(self.metadata.storage_locations.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_STORAGE_LOCATION', 'Preservation System')
    def test_populate_storage_location_with_default(self):
        add_related_models({}, self.metadata, StorageLocation)

        self.assertEqual(self.metadata.storage_locations.count(), 1)
        self.assertEqual(self.metadata.storage_locations.first().storage_location, 'Preservation System')


class TestFormToRights(TestCase):
    ''' Test the conversion from the metadata form to caais.models.Rights objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()
        self.other_rights_type, _ = RightsType.objects.get_or_create(name='Other')

    def test_no_rights(self):
        form_data = {}

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 0)

    def test_no_rights_empty_list(self):
        ''' Test an empty set of rights. The key exist, but the list is
        empty.
        '''
        form_data = {'formset-rights': []}

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 0)

    def test_no_rights_empty_data(self):
        ''' Test various "empty" rights that should not yield an identifier.
        '''
        form_data = {
            'formset-rights': [
                None,
                {},
                {
                    'rights_type': None,
                    'rights_value': '',
                    'rights_note': '',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 0)

    def test_populate_one_rights_statement(self):
        rights_type, created = RightsType.objects.get_or_create(name='Copyright')

        form_data = {
            'formset-rights': [
                {
                    'rights_type': rights_type,
                    'rights_value': 'Until 2043',
                    'rights_note': 'My note',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)

        rights = self.metadata.rights.first()
        self.assertTrue(rights.rights_type)
        self.assertEqual(rights.rights_type, rights_type)
        self.assertEqual(rights.rights_value, 'Until 2043')
        self.assertEqual(rights.rights_note, 'My note')

        if created:
            rights_type.delete()

    def test_populate_multiple_rights(self):
        rights_type_1, created_1 = RightsType.objects.get_or_create(name='Copyright')
        rights_type_2, created_2 = RightsType.objects.get_or_create(name='Statute')

        form_data = {
            'formset-rights': [
                {
                    'rights_type': rights_type_1,
                    'rights_value': 'Copyright value',
                    'rights_note': 'My note',
                },
                {
                    'rights_type': rights_type_2,
                    'rights_value': 'Statute value',
                    'rights_note': '',
                },
                {
                    'rights_type': None,
                    'rights_value': 'No specific rights',
                    'rights_note': '',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 3)

        rights_1, rights_2, rights_3 = self.metadata.rights.all()

        self.assertEqual(rights_1.rights_type, rights_type_1)
        self.assertEqual(rights_1.rights_value, 'Copyright value')
        self.assertEqual(rights_1.rights_note, 'My note')

        self.assertEqual(rights_2.rights_type, rights_type_2)
        self.assertEqual(rights_2.rights_value, 'Statute value')
        self.assertEqual(rights_2.rights_note, '')

        self.assertFalse(rights_3.rights_type)
        self.assertEqual(rights_3.rights_value, 'No specific rights')
        self.assertEqual(rights_3.rights_note, '')

        if created_1:
            rights_type_1.delete()
        if created_2:
            rights_type_2.delete()

    def test_populate_rights_ignore_duplicates(self):
        rights_type, created = RightsType.objects.get_or_create(name='Copyright')

        form_data = {
            'formset-rights': [
                {
                    'rights_type': rights_type,
                    'rights_value': 'Value',
                },
                {
                    'rights_type': rights_type,
                    'rights_value': 'Value',
                },
                {
                    'rights_type': rights_type,
                    'rights_value': 'Value',
                    'rights_note': '',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)

        if created:
            rights_type.delete()

    def test_populate_rights_no_rights_type(self):
        form_data = {
            'formset-rights': [
                {
                    'rights_note': 'Notes notes notes',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)
        rights = self.metadata.rights.first()
        self.assertFalse(rights.rights_type)
        self.assertEqual(rights.rights_value, '')
        self.assertEqual(rights.rights_note, 'Notes notes notes')

    def test_populate_rights_other_rights_type(self):
        form_data = {
            'formset-rights': [
                {
                    'rights_type': self.other_rights_type,
                    'other_rights_type': 'Test Type',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)
        rights = self.metadata.rights.first()
        self.assertEqual(rights.rights_type, self.other_rights_type)
        self.assertEqual(rights.rights_value, '')
        self.assertEqual(rights.rights_note, "Type of rights was noted as 'Test Type'")

    def test_populate_rights_other_rights_type_with_note(self):
        form_data = {
            'formset-rights': [
                {
                    'rights_type': self.other_rights_type,
                    'other_rights_type': 'Test Type',
                    'rights_note': 'Could not determine rights at this time.'
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)
        rights = self.metadata.rights.first()
        self.assertEqual(rights.rights_type, self.other_rights_type)
        self.assertEqual(rights.rights_value, '')
        self.assertEqual(
            rights.rights_note,
            "Type of rights was noted as 'Test Type'. Could not determine rights at this time."
        )

    def test_populate_rights_prefer_rights_type_over_other(self):
        rights_type, created = RightsType.objects.get_or_create(name='Not known')

        form_data = {
            'formset-rights': [
                {
                    'rights_type': rights_type,
                    'other_rights_type': 'Unknown',
                },
            ]
        }

        add_rights(form_data, self.metadata)

        self.assertEqual(self.metadata.rights.count(), 1)
        rights = self.metadata.rights.first()
        self.assertTrue(rights.rights_type)
        self.assertEqual(rights.rights_type.name, 'Not known')
        self.assertEqual(rights.rights_value, '')
        self.assertEqual(rights.rights_note, '')

        if created:
            rights_type.delete()


class TestFormToPreservationRequirements(TestCase):
    ''' Test the conversion from the metadata form to caais.models.PreservationRequirements
    objects.

    There is no way to add preservation requirements from the form; if any defaults are set for
    preservation requirements, one new preservation requirement will be added for each submission
    received.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', '')
    def test_populate_preservation_requirements_no_default(self):
        add_related_models({}, self.metadata, PreservationRequirements)

        self.assertEqual(self.metadata.preservation_requirements.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', 'None Required')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', '')
    def test_populate_preservation_requirements_only_type(self):
        add_related_models({}, self.metadata, PreservationRequirements)

        self.assertEqual(self.metadata.preservation_requirements.count(), 1)
        req = self.metadata.preservation_requirements.first()
        self.assertTrue(req.preservation_requirements_type)
        self.assertEqual(req.preservation_requirements_type.name, 'None Required')
        self.assertFalse(req.preservation_requirements_value)
        self.assertFalse(req.preservation_requirements_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', 'Value Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', '')
    def test_populate_preservation_requirements_only_value(self):
        add_related_models({}, self.metadata, PreservationRequirements)

        self.assertEqual(self.metadata.preservation_requirements.count(), 1)
        req = self.metadata.preservation_requirements.first()
        self.assertFalse(req.preservation_requirements_type)
        self.assertEqual(req.preservation_requirements_value, 'Value Here')
        self.assertFalse(req.preservation_requirements_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', 'Note Here')
    def test_populate_preservation_requirements_only_value(self):
        add_related_models({}, self.metadata, PreservationRequirements)

        self.assertEqual(self.metadata.preservation_requirements.count(), 1)
        req = self.metadata.preservation_requirements.first()
        self.assertFalse(req.preservation_requirements_type)
        self.assertFalse(req.preservation_requirements_value)
        self.assertEqual(req.preservation_requirements_note, 'Note Here')

    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE', 'Type Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE', 'Value Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE', 'Note Here')
    def test_populate_preservation_requirements_all_defaults(self):
        add_related_models({}, self.metadata, PreservationRequirements)

        self.assertEqual(self.metadata.preservation_requirements.count(), 1)
        req = self.metadata.preservation_requirements.first()
        self.assertTrue(req.preservation_requirements_type)
        self.assertEqual(req.preservation_requirements_type.name, 'Type Here')
        self.assertEqual(req.preservation_requirements_value, 'Value Here')
        self.assertEqual(req.preservation_requirements_note, 'Note Here')


class TestFormToAppraisal(TestCase):
    ''' Test the conversion from the metadata form to caais.models.Appraisal
    objects.

    There is no way to add appraisals from the form; if any defaults are set for appraisals, one new
    appraisal will be added for each submission received.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_NOTE', '')
    def test_populate_appraisal_no_default(self):
        add_related_models({}, self.metadata, Appraisal)

        self.assertEqual(self.metadata.appraisals.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_TYPE', 'Type Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_NOTE', '')
    def test_populate_appraisal_only_type(self):
        add_related_models({}, self.metadata, Appraisal)

        self.assertEqual(self.metadata.appraisals.count(), 1)
        appraisal = self.metadata.appraisals.first()
        self.assertTrue(appraisal.appraisal_type)
        self.assertEqual(appraisal.appraisal_type.name, 'Type Here')
        self.assertFalse(appraisal.appraisal_value)
        self.assertFalse(appraisal.appraisal_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_VALUE', 'Value Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_NOTE', '')
    def test_populate_appraisal_only_value(self):
        add_related_models({}, self.metadata, Appraisal)

        self.assertEqual(self.metadata.appraisals.count(), 1)
        appraisal = self.metadata.appraisals.first()
        self.assertFalse(appraisal.appraisal_type)
        self.assertEqual(appraisal.appraisal_value, 'Value Here')
        self.assertFalse(appraisal.appraisal_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_VALUE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_NOTE', 'Note Here')
    def test_populate_appraisal_only_value(self):
        add_related_models({}, self.metadata, Appraisal)

        self.assertEqual(self.metadata.appraisals.count(), 1)
        appraisal = self.metadata.appraisals.first()
        self.assertFalse(appraisal.appraisal_type)
        self.assertFalse(appraisal.appraisal_value)
        self.assertEqual(appraisal.appraisal_note, 'Note Here')

    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_TYPE', 'Type Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_VALUE', 'Value Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_APPRAISAL_NOTE', 'Note Here')
    def test_populate_appraisal_all_defaults(self):
        add_related_models({}, self.metadata, Appraisal)

        self.assertEqual(self.metadata.appraisals.count(), 1)
        appraisal = self.metadata.appraisals.first()
        self.assertTrue(appraisal.appraisal_type)
        self.assertEqual(appraisal.appraisal_type.name, 'Type Here')
        self.assertEqual(appraisal.appraisal_value, 'Value Here')
        self.assertEqual(appraisal.appraisal_note, 'Note Here')


class TestFormToAssociatedDocumentation(TestCase):
    ''' Test the conversion from the metadata form to caais.models.AssociatedDocumentation
    objects.

    There is no way to add associated documentation from the form; if any defaults are set for
    associated documentation, one new document will be added for each submission received.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', '')
    def test_populate_associated_documentation_no_default(self):
        add_related_models({}, self.metadata, AssociatedDocumentation)

        self.assertEqual(self.metadata.associated_documentation.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', 'Type Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', '')
    def test_populate_associated_documentation_only_type(self):
        add_related_models({}, self.metadata, AssociatedDocumentation)

        self.assertEqual(self.metadata.associated_documentation.count(), 1)
        doc = self.metadata.associated_documentation.first()
        self.assertTrue(doc.associated_documentation_type)
        self.assertEqual(doc.associated_documentation_type.name, 'Type Here')
        self.assertFalse(doc.associated_documentation_title)
        self.assertFalse(doc.associated_documentation_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', 'Title Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', '')
    def test_populate_associated_documentation_only_title(self):
        add_related_models({}, self.metadata, AssociatedDocumentation)

        self.assertEqual(self.metadata.associated_documentation.count(), 1)
        doc = self.metadata.associated_documentation.first()
        self.assertFalse(doc.associated_documentation_type)
        self.assertEqual(doc.associated_documentation_title, 'Title Here')
        self.assertFalse(doc.associated_documentation_note)

    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', 'Note Here')
    def test_populate_associated_documentation_only_title(self):
        add_related_models({}, self.metadata, AssociatedDocumentation)

        self.assertEqual(self.metadata.associated_documentation.count(), 1)
        doc = self.metadata.associated_documentation.first()
        self.assertFalse(doc.associated_documentation_type)
        self.assertFalse(doc.associated_documentation_title)
        self.assertEqual(doc.associated_documentation_note, 'Note Here')

    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE', 'Type Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE', 'Title Here')
    @patch('django.conf.settings.CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE', 'Note Here')
    def test_populate_associated_documentation_all_defaults(self):
        add_related_models({}, self.metadata, AssociatedDocumentation)

        self.assertEqual(self.metadata.associated_documentation.count(), 1)
        doc = self.metadata.associated_documentation.first()
        self.assertTrue(doc.associated_documentation_type)
        self.assertEqual(doc.associated_documentation_type.name, 'Type Here')
        self.assertEqual(doc.associated_documentation_title, 'Title Here')
        self.assertEqual(doc.associated_documentation_note, 'Note Here')


class TestFormToEvent(TestCase):
    ''' Test the addition of a submission-type Event to the metadata object.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch.object(timezone, 'now', return_value=datetime(2023, 9, 29, 9, 0, 0, tzinfo=timezone.get_current_timezone()))
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE', 'Submitted')
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE', '')
    def test_add_submission_event_only_mandatory_default(self, timezone_now__patch):
        add_submission_event(self.metadata)

        self.assertEqual(self.metadata.events.count(), 1)

        event = self.metadata.events.first()
        self.assertEqual(event.event_type.name, 'Submitted')
        self.assertEqual(event.event_date, timezone_now__patch.return_value)
        self.assertEqual(event.event_agent, '')
        self.assertEqual(event.event_note, '')

    @patch.object(timezone, 'now', return_value=datetime(2023, 10, 3, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE', 'Submission')
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT', 'Record Transfer')
    @patch('django.conf.settings.CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE', 'Submitted by user via Record Transfer')
    def test_add_submission_event_all_defaults(self, timezone_now__patch):
        add_submission_event(self.metadata)

        self.assertEqual(self.metadata.events.count(), 1)

        event = self.metadata.events.first()
        self.assertEqual(event.event_type.name, 'Submission')
        self.assertEqual(event.event_date, timezone_now__patch.return_value)
        self.assertEqual(event.event_agent, 'Record Transfer')
        self.assertEqual(event.event_note, 'Submitted by user via Record Transfer')


class TestFormToGeneralNote(TestCase):
    ''' Test the conversion from the metadata form to caais.models.GeneralNote
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch('django.conf.settings.CAAIS_DEFAULT_GENERAL_NOTE', '')
    def test_populate_general_note_no_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, GeneralNote)

        self.assertEqual(self.metadata.general_notes.count(), 0)

    @patch('django.conf.settings.CAAIS_DEFAULT_GENERAL_NOTE', 'Default note')
    def test_populate_general_note_with_default(self):
        form_data = {}

        add_related_models(form_data, self.metadata, GeneralNote)

        self.assertEqual(self.metadata.general_notes.first().general_note, 'Default note')

    @patch('django.conf.settings.CAAIS_DEFAULT_GENERAL_NOTE', 'Default note')
    def test_populate_general_note_with_default_prefer_form(self):
        form_data = {
            'general_note': 'My note'
        }

        add_related_models(form_data, self.metadata, GeneralNote)

        self.assertEqual(self.metadata.general_notes.first().general_note, 'My note')


class TestFormToDatesOfCreationOrRevision(TestCase):
    ''' Test the conversion from the metadata form to caais.models.DatesOfCreationOrRevision
    objects.
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        self.metadata = Metadata.objects.create()

    @patch.object(timezone, 'now', return_value=datetime(2023, 10, 24, 9, 33, 0, tzinfo=timezone.get_current_timezone()))
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_TYPE', 'Creation')
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_AGENT', '')
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_NOTE', '')
    def test_add_creation_event_only_mandatory_default(self, timezone_now__patch):
        add_date_of_creation(self.metadata)

        self.assertEqual(self.metadata.dates_of_creation_or_revision.count(), 1)

        date = self.metadata.dates_of_creation_or_revision.first()
        self.assertTrue(date.creation_or_revision_type)
        self.assertEqual(date.creation_or_revision_type.name, 'Creation')
        self.assertEqual(date.creation_or_revision_date, timezone_now__patch.return_value)
        self.assertEqual(date.creation_or_revision_agent, '')
        self.assertEqual(date.creation_or_revision_note, '')

    @patch.object(timezone, 'now', return_value=datetime(2023, 10, 24, 9, 33, 0, tzinfo=timezone.get_current_timezone()))
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_TYPE', 'Creation')
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_AGENT', 'Transfer Application')
    @patch('django.conf.settings.CAAIS_DEFAULT_CREATION_NOTE', 'Date submission was created')
    def test_add_creation_event_all_defaults(self, timezone_now__patch):
        add_date_of_creation(self.metadata)

        self.assertEqual(self.metadata.dates_of_creation_or_revision.count(), 1)

        date = self.metadata.dates_of_creation_or_revision.first()
        self.assertTrue(date.creation_or_revision_type)
        self.assertEqual(date.creation_or_revision_type.name, 'Creation')
        self.assertEqual(date.creation_or_revision_date, timezone_now__patch.return_value)
        self.assertEqual(date.creation_or_revision_agent, 'Transfer Application')
        self.assertEqual(date.creation_or_revision_note, 'Date submission was created')
