from unittest.mock import patch
from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from caais.export import ExportVersion
from caais.models import (
    AcquisitionMethod,
    Appraisal,
    AppraisalType,
    ArchivalUnit,
    AssociatedDocumentation,
    AssociatedDocumentationType,
    CarrierType,
    ContentType,
    DateOfCreationOrRevision,
    DateOfCreationOrRevisionType,
    DispositionAuthority,
    Event,
    EventType,
    ExtentStatement,
    ExtentType,
    GeneralNote,
    Identifier,
    LanguageOfMaterial,
    Metadata,
    PreliminaryCustodialHistory,
    PreliminaryScopeAndContent,
    PreservationRequirements,
    PreservationRequirementsType,
    Rights,
    RightsType,
    SourceConfidentiality,
    SourceOfMaterial,
    SourceRole,
    SourceType,
    Status,
    StorageLocation,
)


class TestIdentifierManager(TestCase):
    ''' Testing manager for metadata.identifiers
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related_identifiers(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_2 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 2',
            identifier_value='ID VALUE 2',
        )
        identifier_1.save()
        identifier_2.save()

        self.assertEqual(self.metadata.identifiers.count(), 2)

        identifier_1.delete()
        identifier_2.delete()


    def test_get_accession_identifier_exists(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE',
            identifier_value='ID VALUE',
        )
        identifier_2 = Identifier(
            metadata=self.metadata,
            identifier_type='Accession Identifier',
            identifier_value='A2023-001',
        )
        identifier_1.save()
        identifier_2.save()

        accession_id = self.metadata.identifiers.accession_identifier()

        self.assertTrue(accession_id)
        self.assertEqual(accession_id.identifier_value, 'A2023-001')
        self.assertEqual(accession_id.identifier_type, 'Accession Identifier')

        identifier_1.delete()
        identifier_2.delete()


    def test_get_accession_identifier_not_exists(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE',
            identifier_value='ID VALUE',
        )
        identifier_1.save()

        accession_id = self.metadata.identifiers.accession_identifier()

        self.assertFalse(accession_id)

        identifier_1.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.identifiers.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_identifier_caais_1_0(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_1.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        # Assure data is as we expect
        self.assertEqual(flat['identifierTypes'], 'ID TYPE 1')
        self.assertEqual(flat['identifierValues'], 'ID VALUE 1')
        self.assertEqual(flat['identifierNotes'], 'ID NOTE 1')


    def test_flatten_multiple_identifier_caais_1_0_(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_2 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 2',
            identifier_value='ID VALUE 2',
        )
        identifier_1.save()
        identifier_2.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['identifierTypes'], 'ID TYPE 1|ID TYPE 2')
        self.assertEqual(flat['identifierValues'], 'ID VALUE 1|ID VALUE 2')
        self.assertEqual(flat['identifierNotes'], 'ID NOTE 1|NULL')

        identifier_1.delete()
        identifier_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_identifier_atom_2_6(self):
        # There are no alternativeIdentifiers in AtoM 2.3
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_1.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['alternativeIdentifierTypes'], 'ID TYPE 1')
        self.assertEqual(flat['alternativeIdentifiers'], 'ID VALUE 1')
        self.assertEqual(flat['alternativeIdentifierNotes'], 'ID NOTE 1')

        identifier_1.delete()


    def test_flatten_multiple_identifier_atom_2_6(self):
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_2 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 2',
            identifier_value='ID VALUE 2',
        )
        identifier_1.save()
        identifier_2.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['alternativeIdentifierTypes'], 'ID TYPE 1|ID TYPE 2')
        self.assertEqual(flat['alternativeIdentifiers'], 'ID VALUE 1|ID VALUE 2')
        self.assertEqual(flat['alternativeIdentifierNotes'], 'ID NOTE 1|NULL')

        identifier_1.delete()
        identifier_2.delete()


    def test_flatten_identifier_with_accession_atom_2_6(self):
        # AtoM should not include an Accession Identifier as an alternative
        # identifier since there is already a column for accessionNumber
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE',
            identifier_value='ID VALUE',
        )
        identifier_2 = Identifier(
            metadata=self.metadata,
            identifier_type='Accession Identifier',
            identifier_value='A2023-001',
        )
        identifier_1.save()
        identifier_2.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['alternativeIdentifierTypes'], 'ID TYPE')
        self.assertEqual(flat['alternativeIdentifiers'], 'ID VALUE')
        self.assertEqual(flat['alternativeIdentifierNotes'], 'NULL')

        identifier_1.delete()
        identifier_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_identifier_atom_2_3(self):
        # There are no alternativeIdentifiers in AtoM 2.3
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_1.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        identifier_1.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_identifier_atom_2_2(self):
        # There are no alternativeIdentifiers in AtoM 2.2
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_1.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        identifier_1.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_identifier_atom_2_1(self):
        # There are no alternativeIdentifiers in AtoM 2.1
        identifier_1 = Identifier(
            metadata=self.metadata,
            identifier_type='ID TYPE 1',
            identifier_value='ID VALUE 1',
            identifier_note='ID NOTE 1',
        )
        identifier_1.save()

        flat = self.metadata.identifiers.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        identifier_1.delete()


class TestArchivalUnitManager(TestCase):
    ''' Testing manager for metadata.archival_units
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related_archival_unit(self):
        unit_1 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit_2 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 2'
        )
        unit_3 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 3'
        )
        unit_1.save()
        unit_2.save()
        unit_3.save()

        self.assertEqual(self.metadata.archival_units.count(), 3)

        unit_1.delete()
        unit_2.delete()
        unit_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.archival_units.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_archival_unit_caais_1_0(self):
        unit_1 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit_1.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['archivalUnits'], 'ARCHIVAL UNIT 1')

        unit_1.delete()


    def test_flatten_multiple_archival_unit_caais_1_0(self):
        unit_1 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit_2 = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 2'
        )
        unit_1.save()
        unit_2.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.CAAIS_1_0)

        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['archivalUnits'], 'ARCHIVAL UNIT 1|ARCHIVAL UNIT 2')


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_archival_unit_atom_2_6(self):
        # There are no archival units in AtoM 2.6
        unit = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_archival_unit_atom_2_3(self):
        # There are no archival units in AtoM 2.3
        unit = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_archival_unit_atom_2_2(self):
        # There are no archival units in AtoM 2.2
        unit = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_archival_unit_atom_2_1(self):
        # There are no archival units in AtoM 2.1
        unit = ArchivalUnit(
            metadata=self.metadata,
            archival_unit='ARCHIVAL UNIT 1'
        )
        unit.save()

        flat = self.metadata.archival_units.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        unit.delete()


class TestDispositionAuthorityManager(TestCase):
    ''' Testing manager for metadata.disposition_authorities
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related_disposition_authority(self):
        unit_1 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit_2 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 2'
        )
        unit_3 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 3'
        )
        unit_1.save()
        unit_2.save()
        unit_3.save()

        self.assertEqual(self.metadata.disposition_authorities.count(), 3)

        unit_1.delete()
        unit_2.delete()
        unit_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.disposition_authorities.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_disposition_authority_caais_1_0(self):
        unit_1 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit_1.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['dispositionAuthorities'], 'DISPOSITION AUTHORITY 1')

        unit_1.delete()


    def test_flatten_multiple_disposition_authority_caais_1_0(self):
        unit_1 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit_2 = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 2'
        )
        unit_1.save()
        unit_2.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['dispositionAuthorities'], 'DISPOSITION AUTHORITY 1|DISPOSITION AUTHORITY 2')


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_disposition_authority_atom_2_6(self):
        # There are no disposition authorities in AtoM 2.6
        unit = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_disposition_authority_atom_2_3(self):
        # There are no disposition authorities in AtoM 2.3
        unit = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_disposition_authority_atom_2_2(self):
        # There are no disposition authorities in AtoM 2.2
        unit = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        unit.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_disposition_authority_atom_2_1(self):
        # There are no disposition authorities in AtoM 2.1
        unit = DispositionAuthority(
            metadata=self.metadata,
            disposition_authority='DISPOSITION AUTHORITY 1'
        )
        unit.save()

        flat = self.metadata.disposition_authorities.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        unit.delete()


class TestSourceOfMaterialManager(TestCase):
    ''' Testing manager for metadata.source_of_materials
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()

    def test_access_related_sources(self):
        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_name='NAME 1'
        )
        source_2 = SourceOfMaterial(
            metadata=self.metadata,
            source_name='NAME 2'
        )
        source_3 = SourceOfMaterial(
            metadata=self.metadata,
            source_name='NAME 3'
        )
        source_1.save()
        source_2.save()
        source_3.save()

        self.assertEqual(self.metadata.source_of_materials.count(), 3)

        source_1.delete()
        source_2.delete()
        source_3.delete()


    def test_flatten_address_line_1_caais(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_1='123 Example Street'
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)

        self.assertEqual(flat['sourceStreetAddress'], '123 Example Street')


    def test_flatten_address_line_2_caais(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_2='123 Example Street'
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)

        self.assertEqual(flat['sourceStreetAddress'], '123 Example Street')


    def test_flatten_address_line_1_and_2_caais(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_1='123 Example Street',
            address_line_2='Apt. 14',
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)

        self.assertEqual(flat['sourceStreetAddress'], '123 Example Street, Apt. 14')


    def test_flatten_address_line_1_atom(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_1='123 Example Street'
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)

        self.assertEqual(flat['donorStreetAddress'], '123 Example Street')


    def test_flatten_address_line_2_atom(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_2='123 Example Street'
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)

        self.assertEqual(flat['donorStreetAddress'], '123 Example Street')


    def test_flatten_address_line_1_and_2_atom(self):
        source = SourceOfMaterial(
            metadata=self.metadata,
            address_line_1='123 Example Street',
            address_line_2='Apt. 14',
        )
        source.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)

        self.assertEqual(flat['donorStreetAddress'], '123 Example Street, Apt. 14')


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_source_caais_1_0(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )

        source_1.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['sourceType'], 'Individual')
        self.assertEqual(flat['sourceName'], 'SOURCE NAME')
        self.assertEqual(flat['sourceContactPerson'], 'CONTACT NAME')
        self.assertEqual(flat['sourceJobTitle'], 'JOB TITLE')
        self.assertEqual(flat['sourceOrganization'], 'ORGANIZATION')
        self.assertEqual(flat['sourceStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['sourceCity'], 'CITY')
        self.assertEqual(flat['sourceRegion'], 'REGION')
        self.assertEqual(flat['sourcePostalCode'], 'R4R 4R4')
        self.assertEqual(flat['sourceCountry'], 'CA')
        self.assertEqual(flat['sourcePhoneNumber'], '111 111-1111')
        self.assertEqual(flat['sourceEmail'], 'user@example.com')
        self.assertEqual(flat['sourceRole'], 'Custodian')
        self.assertEqual(flat['sourceNote'], 'SOURCE NOTE')
        self.assertEqual(flat['sourceConfidentiality'], 'Public')

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()


    def test_flatten_multiple_source_caais_1_0(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_2 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 2',
            address_line_1='123 Example Street',
        )
        source_1.save()
        source_2.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['sourceType'], 'Individual|Individual')
        self.assertEqual(flat['sourceName'], 'SOURCE NAME 1|SOURCE NAME 2')
        self.assertEqual(flat['sourceContactPerson'], 'CONTACT NAME|NULL')
        self.assertEqual(flat['sourceJobTitle'], 'JOB TITLE|NULL')
        self.assertEqual(flat['sourceOrganization'], 'ORGANIZATION|NULL')
        self.assertEqual(flat['sourceStreetAddress'], 'LINE 1, LINE 2|123 Example Street')
        self.assertEqual(flat['sourceCity'], 'CITY|NULL')
        self.assertEqual(flat['sourceRegion'], 'REGION|NULL')
        self.assertEqual(flat['sourcePostalCode'], 'R4R 4R4|NULL')
        self.assertEqual(flat['sourceCountry'], 'CA|NULL')
        self.assertEqual(flat['sourcePhoneNumber'], '111 111-1111|NULL')
        self.assertEqual(flat['sourceEmail'], 'user@example.com|NULL')
        self.assertEqual(flat['sourceRole'], 'Custodian|NULL')
        self.assertEqual(flat['sourceNote'], 'SOURCE NOTE|NULL')
        self.assertEqual(flat['sourceConfidentiality'], 'Public|NULL')

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()
        source_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_source_atom_2_6(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_1.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['donorName'], 'SOURCE NAME 1')
        self.assertEqual(flat['donorStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['donorCity'], 'CITY')
        self.assertEqual(flat['donorRegion'], 'REGION')
        self.assertEqual(flat['donorCountry'], 'CA')
        self.assertEqual(flat['donorPostalCode'], 'R4R 4R4')
        self.assertEqual(flat['donorTelephone'], '111 111-1111')
        self.assertEqual(flat['donorFax'], '')
        self.assertEqual(flat['donorEmail'], 'user@example.com')
        self.assertIn('Individual', flat['donorNote'])
        self.assertIn('Custodian', flat['donorNote'])
        self.assertIn('Public', flat['donorNote'])
        self.assertIn('SOURCE NOTE', flat['donorNote'])
        self.assertEqual(flat['donorContactPerson'], 'CONTACT NAME')

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()


    def test_flatten_multiple_source_atom_2_6(self):
        # Only one donor is allowed, so the second one will not appear in the
        # flattened metadata
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_2 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 2',
            address_line_1='123 Example Street',
        )
        source_1.save()
        source_2.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['donorName'], 'SOURCE NAME 1')
        self.assertEqual(flat['donorStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['donorCity'], 'CITY')
        self.assertEqual(flat['donorRegion'], 'REGION')
        self.assertEqual(flat['donorCountry'], 'CA')
        self.assertEqual(flat['donorPostalCode'], 'R4R 4R4')
        self.assertEqual(flat['donorTelephone'], '111 111-1111')
        self.assertEqual(flat['donorFax'], '')
        self.assertEqual(flat['donorEmail'], 'user@example.com')
        self.assertIn('Individual', flat['donorNote'])
        self.assertIn('Custodian', flat['donorNote'])
        self.assertIn('Public', flat['donorNote'])
        self.assertIn('SOURCE NOTE', flat['donorNote'])
        self.assertEqual(flat['donorContactPerson'], 'CONTACT NAME')

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()
        source_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_source_atom_2_3(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_1.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['donorName'], 'SOURCE NAME 1')
        self.assertEqual(flat['donorStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['donorCity'], 'CITY')
        self.assertEqual(flat['donorRegion'], 'REGION')
        self.assertEqual(flat['donorCountry'], 'CA')
        self.assertEqual(flat['donorPostalCode'], 'R4R 4R4')
        self.assertEqual(flat['donorTelephone'], '111 111-1111')
        self.assertEqual(flat['donorEmail'], 'user@example.com')
        # These fields were added in AtoM 2.6 (not avail. in 2.3)
        self.assertNotIn('donorFax', flat)
        self.assertNotIn('donorNote', flat)
        self.assertNotIn('donorContactPerson', flat)

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_source_atom_2_2(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_1.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['donorName'], 'SOURCE NAME 1')
        self.assertEqual(flat['donorStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['donorCity'], 'CITY')
        self.assertEqual(flat['donorRegion'], 'REGION')
        self.assertEqual(flat['donorCountry'], 'CA')
        self.assertEqual(flat['donorPostalCode'], 'R4R 4R4')
        self.assertEqual(flat['donorTelephone'], '111 111-1111')
        self.assertEqual(flat['donorEmail'], 'user@example.com')
        # These fields were added in AtoM 2.6 (not avail. in 2.2)
        self.assertNotIn('donorFax', flat)
        self.assertNotIn('donorNote', flat)
        self.assertNotIn('donorContactPerson', flat)

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_source_atom_2_1(self):
        source_type = SourceType(name='Individual')
        source_role = SourceRole(name='Custodian')
        source_conf = SourceConfidentiality(name='Public')
        source_type.save()
        source_role.save()
        source_conf.save()

        source_1 = SourceOfMaterial(
            metadata=self.metadata,
            source_type=source_type,
            source_name='SOURCE NAME 1',
            contact_name='CONTACT NAME',
            job_title='JOB TITLE',
            organization='ORGANIZATION',
            phone_number='111 111-1111',
            email_address='user@example.com',
            address_line_1='LINE 1',
            address_line_2='LINE 2',
            city='CITY',
            region='REGION',
            postal_or_zip_code='R4R 4R4',
            country='CA',
            source_role=source_role,
            source_note='SOURCE NOTE',
            source_confidentiality=source_conf,
        )
        source_1.save()

        flat = self.metadata.source_of_materials.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['donorName'], 'SOURCE NAME 1')
        self.assertEqual(flat['donorStreetAddress'], 'LINE 1, LINE 2')
        self.assertEqual(flat['donorCity'], 'CITY')
        self.assertEqual(flat['donorRegion'], 'REGION')
        self.assertEqual(flat['donorCountry'], 'CA')
        self.assertEqual(flat['donorPostalCode'], 'R4R 4R4')
        self.assertEqual(flat['donorTelephone'], '111 111-1111')
        self.assertEqual(flat['donorEmail'], 'user@example.com')
        # These fields were added in AtoM 2.6 (not avail. in 2.1)
        self.assertNotIn('donorFax', flat)
        self.assertNotIn('donorNote', flat)
        self.assertNotIn('donorContactPerson', flat)

        source_type.delete()
        source_role.delete()
        source_conf.delete()
        source_1.delete()


class TestPreliminaryCustodialHistoryManager(TestCase):
    ''' Testing manager for metadata.preliminary_custodial_histories
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()

    def test_access_related_histories(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_3 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 3'
        )
        history_1.save()
        history_2.save()
        history_3.save()

        self.assertEqual(self.metadata.preliminary_custodial_histories.count(), 3)

        history_1.delete()
        history_2.delete()
        history_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_history_caais_1_0(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_1.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preliminaryCustodialHistory'], 'HISTORY 1')

        history_1.delete()


    def test_flatten_multiple_history_caais_1_0(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_1.save()
        history_2.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preliminaryCustodialHistory'], 'HISTORY 1|HISTORY 2')

        history_1.delete()
        history_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_history_atom_2_6(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_1.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['archivalHistory'], 'HISTORY 1')

        history_1.delete()


    def test_flatten_multiple_history_atom_2_6(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_1.save()
        history_2.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['archivalHistory'], '* HISTORY 1\n* HISTORY 2')

        history_1.delete()
        history_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_history_atom_2_3(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_1.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['archivalHistory'], 'HISTORY 1')

        history_1.delete()


    def test_flatten_multiple_history_atom_2_3(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_1.save()
        history_2.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['archivalHistory'], '* HISTORY 1\n* HISTORY 2')

        history_1.delete()
        history_2.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_history_atom_2_2(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_1.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['archivalHistory'], 'HISTORY 1')

        history_1.delete()


    def test_flatten_multiple_history_atom_2_2(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_1.save()
        history_2.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['archivalHistory'], '* HISTORY 1\n* HISTORY 2')

        history_1.delete()
        history_2.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_history_atom_2_1(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_1.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['archivalHistory'], 'HISTORY 1')

        history_1.delete()


    def test_flatten_multiple_history_atom_2_1(self):
        history_1 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 1'
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=self.metadata,
            preliminary_custodial_history='HISTORY 2'
        )
        history_1.save()
        history_2.save()

        flat = self.metadata.preliminary_custodial_histories.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['archivalHistory'], '* HISTORY 1\n* HISTORY 2')

        history_1.delete()
        history_2.delete()


class TestExtentStatementManager(TestCase):
    ''' Testing manager for metadata.extent_statements
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        extent_1 = ExtentStatement(metadata=self.metadata)
        extent_2 = ExtentStatement(metadata=self.metadata)
        extent_3 = ExtentStatement(metadata=self.metadata)
        extent_1.save()
        extent_2.save()
        extent_3.save()

        self.assertEqual(self.metadata.extent_statements.count(), 3)

        extent_1.delete()
        extent_2.delete()
        extent_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.extent_statements.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_extent_caais_1_0(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        objects = (extent_type, content_type, carrier_type, extent_1)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['extentTypes'], 'Extent Received')
        self.assertEqual(flat['quantityAndUnitOfMeasure'], '3 FILES')
        self.assertEqual(flat['contentTypes'], 'Digital Files')
        self.assertEqual(flat['carrierTypes'], 'Digital')
        self.assertEqual(flat['extentNotes'], 'NOTE 1')

        for obj in objects:
            obj.delete()


    def test_flatten_multiple_extent_caais_1_0(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        extent_2 = ExtentStatement(
            metadata=self.metadata,
            quantity_and_unit_of_measure='10 PDFs',
        )
        objects = (extent_type, content_type, carrier_type, extent_1, extent_2)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['extentTypes'], 'Extent Received|NULL')
        self.assertEqual(flat['quantityAndUnitOfMeasure'], '3 FILES|10 PDFs')
        self.assertEqual(flat['contentTypes'], 'Digital Files|NULL')
        self.assertEqual(flat['carrierTypes'], 'Digital|NULL')
        self.assertEqual(flat['extentNotes'], 'NOTE 1|NULL')

        for obj in objects:
            obj.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_extent_atom_2_6(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        objects = (extent_type, content_type, carrier_type, extent_1)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '3 FILES')

        for obj in objects:
            obj.delete()


    def test_flatten_multiple_extent_atom_2_6(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        extent_2 = ExtentStatement(
            metadata=self.metadata,
            quantity_and_unit_of_measure='10 PDFs',
        )
        extent_3 = ExtentStatement(
            metadata=self.metadata,
        )
        objects = (extent_type, content_type, carrier_type, extent_1, extent_2, extent_3)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '* 3 FILES\n* 10 PDFs')

        for obj in objects:
            obj.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_extent_atom_2_3(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        objects = (extent_type, content_type, carrier_type, extent_1)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '3 FILES')

        for obj in objects:
            obj.delete()


    def test_flatten_multiple_extent_atom_2_3(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        extent_2 = ExtentStatement(
            metadata=self.metadata,
            quantity_and_unit_of_measure='10 PDFs',
        )
        extent_3 = ExtentStatement(
            metadata=self.metadata,
        )
        objects = (extent_type, content_type, carrier_type, extent_1, extent_2, extent_3)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '* 3 FILES\n* 10 PDFs')

        for obj in objects:
            obj.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_extent_atom_2_2(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        objects = (extent_type, content_type, carrier_type, extent_1)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '3 FILES')

        for obj in objects:
            obj.delete()


    def test_flatten_multiple_extent_atom_2_2(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        extent_2 = ExtentStatement(
            metadata=self.metadata,
            quantity_and_unit_of_measure='10 PDFs',
        )
        extent_3 = ExtentStatement(
            metadata=self.metadata,
        )
        objects = (extent_type, content_type, carrier_type, extent_1, extent_2, extent_3)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '* 3 FILES\n* 10 PDFs')

        for obj in objects:
            obj.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_extent_atom_2_1(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        objects = (extent_type, content_type, carrier_type, extent_1)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '3 FILES')

        for obj in objects:
            obj.delete()


    def test_flatten_multiple_extent_atom_2_1(self):
        extent_type = ExtentType(name='Extent Received')
        content_type = ContentType(name='Digital Files')
        carrier_type = CarrierType(name='Digital')
        extent_1 = ExtentStatement(
            metadata=self.metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure='3 FILES',
            content_type=content_type,
            carrier_type=carrier_type,
            extent_note='NOTE 1',
        )
        extent_2 = ExtentStatement(
            metadata=self.metadata,
            quantity_and_unit_of_measure='10 PDFs',
        )
        extent_3 = ExtentStatement(
            metadata=self.metadata,
        )
        objects = (extent_type, content_type, carrier_type, extent_1, extent_2, extent_3)

        for obj in objects:
            obj.save()

        flat = self.metadata.extent_statements.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['receivedExtentUnits'], '* 3 FILES\n* 10 PDFs')

        for obj in objects:
            obj.delete()


class TestPreliminaryScopeAndContentManager(TestCase):
    ''' Testing manager for metadata.preliminary_scope_and_contents
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        self.assertEqual(self.metadata.preliminary_scope_and_contents.count(), 2)

        scope_1.delete()
        scope_2.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_scope_caais_1_0(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_1.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preliminaryScopeAndContent'], 'SCOPE 1')

        scope_1.delete()


    def test_flatten_multiple_scope_caais_1_0(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preliminaryScopeAndContent'], 'SCOPE 1|SCOPE 2')

        scope_1.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_scope_atom_2_6(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_1.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1')

        scope_1.delete()


    def test_flatten_multiple_scope_atom_2_6(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1; SCOPE 2')

        scope_1.delete()
        scope_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_scope_atom_2_3(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_1.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1')

        scope_1.delete()


    def test_flatten_multiple_scope_atom_2_3(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1; SCOPE 2')

        scope_1.delete()
        scope_2.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_scope_atom_2_2(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_1.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1')

        scope_1.delete()


    def test_flatten_multiple_scope_atom_2_2(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1; SCOPE 2')

        scope_1.delete()
        scope_2.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_scope_atom_2_1(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_1.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1')

        scope_1.delete()


    def test_flatten_multiple_scope_atom_2_1(self):
        scope_1 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 1'
        )
        scope_2 = PreliminaryScopeAndContent(
            metadata=self.metadata,
            preliminary_scope_and_content='SCOPE 2'
        )
        scope_1.save()
        scope_2.save()

        flat = self.metadata.preliminary_scope_and_contents.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'SCOPE 1; SCOPE 2')

        scope_1.delete()
        scope_2.delete()


class TestLanguageOfMaterialManager(TestCase):
    ''' Testing manager for metadata.language_of_materials
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr'
        )
        language_1.save()
        language_2.save()

        self.assertEqual(self.metadata.language_of_materials.count(), 2)

        language_1.delete()
        language_2.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.language_of_materials.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_language_caais_1_0(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_1.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['languageOfMaterials'], 'en')

        language_1.delete()


    def test_flatten_multiple_language_caais_1_0(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en',
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr',
        )
        language_1.save()
        language_2.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['languageOfMaterials'], 'en|fr')

        language_1.delete()
        language_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_language_atom_2_6(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_1.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en')

        language_1.delete()


    def test_flatten_multiple_language_atom_2_6(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en',
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr',
        )
        language_1.save()
        language_2.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en; fr')

        language_1.delete()
        language_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_language_atom_2_3(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_1.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en')

        language_1.delete()


    def test_flatten_multiple_language_atom_2_3(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en',
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr',
        )
        language_1.save()
        language_2.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en; fr')

        language_1.delete()
        language_2.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_language_atom_2_2(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_1.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en')

        language_1.delete()


    def test_flatten_multiple_language_atom_2_2(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en',
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr',
        )
        language_1.save()
        language_2.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en; fr')

        language_1.delete()
        language_2.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_language_atom_2_1(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en'
        )
        language_1.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en')

        language_1.delete()


    def test_flatten_multiple_language_atom_2_1(self):
        language_1 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='en',
        )
        language_2 = LanguageOfMaterial(
            metadata=self.metadata,
            language_of_material='fr',
        )
        language_1.save()
        language_2.save()

        flat = self.metadata.language_of_materials.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['scopeAndContent'], 'Language(s) of materials: en; fr')

        language_1.delete()
        language_2.delete()


class TestStorageLocationManager(TestCase):
    ''' Testing manager for metadata.storage_locations
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()
        location_2.save()

        self.assertEqual(self.metadata.storage_locations.count(), 2)

        location_1.delete()
        location_2.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.storage_locations.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_location_caais_1_0(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['storageLocation'], 'LOCATION 1')

        location_1.delete()


    def test_flatten_multiple_location_caais_1_0(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 2',
        )
        location_1.save()
        location_2.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['storageLocation'], 'LOCATION 1|LOCATION 2')

        location_1.delete()
        location_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_location_atom_2_6(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['locationInformation'], 'LOCATION 1')

        location_1.delete()


    def test_flatten_multiple_location_atom_2_6(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 2',
        )
        location_1.save()
        location_2.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['locationInformation'], '* LOCATION 1\n* LOCATION 2')

        location_1.delete()
        location_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_location_atom_2_3(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['locationInformation'], 'LOCATION 1')

        location_1.delete()


    def test_flatten_multiple_location_atom_2_3(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 2',
        )
        location_1.save()
        location_2.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['locationInformation'], '* LOCATION 1\n* LOCATION 2')

        location_1.delete()
        location_2.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_location_atom_2_2(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['locationInformation'], 'LOCATION 1')

        location_1.delete()


    def test_flatten_multiple_location_atom_2_2(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 2',
        )
        location_1.save()
        location_2.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['locationInformation'], '* LOCATION 1\n* LOCATION 2')

        location_1.delete()
        location_2.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_location_atom_2_1(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_1.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['locationInformation'], 'LOCATION 1')

        location_1.delete()


    def test_flatten_multiple_location_atom_2_1(self):
        location_1 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 1',
        )
        location_2 = StorageLocation(
            metadata=self.metadata,
            storage_location='LOCATION 2',
        )
        location_1.save()
        location_2.save()

        flat = self.metadata.storage_locations.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['locationInformation'], '* LOCATION 1\n* LOCATION 2')

        location_1.delete()
        location_2.delete()


class TestRightsManager(TestCase):
    ''' Testing manager for metadata.rights
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        rights_1 = Rights(metadata=self.metadata)
        rights_2 = Rights(metadata=self.metadata)
        rights_3 = Rights(metadata=self.metadata)
        rights_1.save()
        rights_2.save()
        rights_3.save()

        self.assertEqual(self.metadata.rights.count(), 3)

        rights_1.delete()
        rights_2.delete()
        rights_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.rights.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_rights_caais_1_0(self):
        rights_type = RightsType(name='Copyright')
        rights_type.save()
        rights_1 = Rights(
            metadata=self.metadata,
            rights_type=rights_type,
            rights_value='RIGHTS VALUE',
            rights_note='RIGHTS NOTE',
        )
        rights_1.save()

        flat = self.metadata.rights.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['rightsTypes'], 'Copyright')
        self.assertEqual(flat['rightsValues'], 'RIGHTS VALUE')
        self.assertEqual(flat['rightsNotes'], 'RIGHTS NOTE')


    def test_flatten_multiple_rights_caais_1_0(self):
        rights_type = RightsType(name='Copyright')
        rights_type.save()
        rights_1 = Rights(
            metadata=self.metadata,
            rights_type=rights_type,
            rights_value='RIGHTS VALUE 1',
            rights_note='RIGHTS NOTE',
        )
        rights_2 = Rights(
            metadata=self.metadata,
            rights_type=rights_type,
            rights_value='RIGHTS VALUE 2',
        )
        rights_1.save()
        rights_2.save()

        flat = self.metadata.rights.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['rightsTypes'], 'Copyright|Copyright')
        self.assertEqual(flat['rightsValues'], 'RIGHTS VALUE 1|RIGHTS VALUE 2')
        self.assertEqual(flat['rightsNotes'], 'RIGHTS NOTE|NULL')


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_rights_atom_2_6(self):
        # There are no rights in AtoM 2.6
        rights_1 = Rights(metadata=self.metadata)
        rights_1.save()

        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        rights_1.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_rights_atom_2_3(self):
        # There are no rights in AtoM 2.3
        rights_1 = Rights(metadata=self.metadata)
        rights_1.save()

        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        rights_1.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_rights_atom_2_2(self):
        # There are no rights in AtoM 2.2
        rights_1 = Rights(metadata=self.metadata)
        rights_1.save()

        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        rights_1.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_rights_atom_2_1(self):
        # There are no rights in AtoM 2.1
        rights_1 = Rights(metadata=self.metadata)
        rights_1.save()

        flat = self.metadata.rights.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        rights_1.delete()


class TestPreservationRequirementsManager(TestCase):
    ''' Testing manager for metadata.preservation_requirements
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        requirements_1 = PreservationRequirements(metadata=self.metadata)
        requirements_2 = PreservationRequirements(metadata=self.metadata)
        requirements_3 = PreservationRequirements(metadata=self.metadata)
        requirements_1.save()
        requirements_2.save()
        requirements_3.save()

        self.assertEqual(self.metadata.preservation_requirements.count(), 3)

        requirements_1.delete()
        requirements_2.delete()
        requirements_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.preservation_requirements.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_requirement_caais_1_0(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_type.save()
        requirements_1.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preservationRequirementsTypes'], 'Preservation Concern')
        self.assertEqual(flat['preservationRequirementsValues'], 'VALUE 1')
        self.assertEqual(flat['preservationRequirementsNotes'], 'NOTE 1')

        requirements_type.delete()
        requirements_1.delete()


    def test_flatten_multiple_requirement_caais_1_0(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_2 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_value='VALUE 2'
        )
        requirements_type.save()
        requirements_1.save()
        requirements_2.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['preservationRequirementsTypes'], 'Preservation Concern|NULL')
        self.assertEqual(flat['preservationRequirementsValues'], 'VALUE 1|VALUE 2')
        self.assertEqual(flat['preservationRequirementsNotes'], 'NOTE 1|NULL')

        requirements_type.delete()
        requirements_1.delete()
        requirements_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_requirement_atom_2_6(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_type.save()
        requirements_1.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], 'VALUE 1. NOTE 1')

        requirements_type.delete()
        requirements_1.delete()


    def test_flatten_multiple_requirement_atom_2_6(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_2 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_value='VALUE 2'
        )
        requirements_3 = PreservationRequirements(
            metadata=self.metadata,
        )
        requirements_type.save()
        requirements_1.save()
        requirements_2.save()
        requirements_3.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], '* VALUE 1. NOTE 1\n* VALUE 2')

        requirements_type.delete()
        requirements_1.delete()
        requirements_2.delete()
        requirements_3.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_requirement_atom_2_3(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_type.save()
        requirements_1.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], 'VALUE 1. NOTE 1')

        requirements_type.delete()
        requirements_1.delete()


    def test_flatten_multiple_requirement_atom_2_3(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_2 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_value='VALUE 2'
        )
        requirements_3 = PreservationRequirements(
            metadata=self.metadata,
        )
        requirements_type.save()
        requirements_1.save()
        requirements_2.save()
        requirements_3.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], '* VALUE 1. NOTE 1\n* VALUE 2')

        requirements_type.delete()
        requirements_1.delete()
        requirements_2.delete()
        requirements_3.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_requirement_atom_2_2(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_type.save()
        requirements_1.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], 'VALUE 1. NOTE 1')

        requirements_type.delete()
        requirements_1.delete()


    def test_flatten_multiple_requirement_atom_2_2(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_2 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_value='VALUE 2'
        )
        requirements_3 = PreservationRequirements(
            metadata=self.metadata,
        )
        requirements_type.save()
        requirements_1.save()
        requirements_2.save()
        requirements_3.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], '* VALUE 1. NOTE 1\n* VALUE 2')

        requirements_type.delete()
        requirements_1.delete()
        requirements_2.delete()
        requirements_3.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_requirement_atom_2_1(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_type.save()
        requirements_1.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], 'VALUE 1. NOTE 1')

        requirements_type.delete()
        requirements_1.delete()


    def test_flatten_multiple_requirement_atom_2_1(self):
        requirements_type = PreservationRequirementsType(name='Preservation Concern')
        requirements_1 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_type=requirements_type,
            preservation_requirements_value='VALUE 1',
            preservation_requirements_note='NOTE 1'
        )
        requirements_2 = PreservationRequirements(
            metadata=self.metadata,
            preservation_requirements_value='VALUE 2'
        )
        requirements_3 = PreservationRequirements(
            metadata=self.metadata,
        )
        requirements_type.save()
        requirements_1.save()
        requirements_2.save()
        requirements_3.save()

        flat = self.metadata.preservation_requirements.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['processingNotes'], '* VALUE 1. NOTE 1\n* VALUE 2')

        requirements_type.delete()
        requirements_1.delete()
        requirements_2.delete()
        requirements_3.delete()


class TestAppraisalManager(TestCase):
    ''' Testing manager for metadata.appraisals
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        appraisal_1 = Appraisal(metadata=self.metadata)
        appraisal_2 = Appraisal(metadata=self.metadata)
        appraisal_3 = Appraisal(metadata=self.metadata)
        appraisal_1.save()
        appraisal_2.save()
        appraisal_3.save()

        self.assertEqual(self.metadata.appraisals.count(), 3)

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.appraisals.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_appraisal_caais_1_0(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_1.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['appraisalTypes'], 'Archival Appraisal')
        self.assertEqual(flat['appraisalValues'], 'APPRAISAL 1')
        self.assertEqual(flat['appraisalNotes'], 'NOTE 1')

        appraisal_1.delete()
        appraisal_type.delete()


    def test_flatten_multiple_appraisal_caais_1_0(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_2 = Appraisal(
            metadata=self.metadata,
            appraisal_value='APPRAISAL 2',
        )
        appraisal_1.save()
        appraisal_2.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['appraisalTypes'], 'Archival Appraisal|NULL')
        self.assertEqual(flat['appraisalValues'], 'APPRAISAL 1|APPRAISAL 2')
        self.assertEqual(flat['appraisalNotes'], 'NOTE 1|NULL')

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_type.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_appraisal_atom_2_6(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_1.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['appraisal'], 'APPRAISAL 1. NOTE 1')

        appraisal_1.delete()
        appraisal_type.delete()


    def test_flatten_multiple_appraisal_atom_2_6(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_2 = Appraisal(
            metadata=self.metadata,
            appraisal_value='APPRAISAL 2',
        )
        appraisal_3 = Appraisal(
            metadata=self.metadata,
        )
        appraisal_1.save()
        appraisal_2.save()
        appraisal_3.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat['appraisal'], '* APPRAISAL 1. NOTE 1\n* APPRAISAL 2')

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_3.delete()
        appraisal_type.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_appraisal_atom_2_3(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_1.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['appraisal'], 'APPRAISAL 1. NOTE 1')

        appraisal_1.delete()
        appraisal_type.delete()


    def test_flatten_multiple_appraisal_atom_2_3(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_2 = Appraisal(
            metadata=self.metadata,
            appraisal_value='APPRAISAL 2',
        )
        appraisal_3 = Appraisal(
            metadata=self.metadata,
        )
        appraisal_1.save()
        appraisal_2.save()
        appraisal_3.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat['appraisal'], '* APPRAISAL 1. NOTE 1\n* APPRAISAL 2')

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_3.delete()
        appraisal_type.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_appraisal_atom_2_2(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_1.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['appraisal'], 'APPRAISAL 1. NOTE 1')

        appraisal_1.delete()
        appraisal_type.delete()


    def test_flatten_multiple_appraisal_atom_2_2(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_2 = Appraisal(
            metadata=self.metadata,
            appraisal_value='APPRAISAL 2',
        )
        appraisal_3 = Appraisal(
            metadata=self.metadata,
        )
        appraisal_1.save()
        appraisal_2.save()
        appraisal_3.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat['appraisal'], '* APPRAISAL 1. NOTE 1\n* APPRAISAL 2')

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_3.delete()
        appraisal_type.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_appraisal_atom_2_1(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_1.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['appraisal'], 'APPRAISAL 1. NOTE 1')

        appraisal_1.delete()
        appraisal_type.delete()


    def test_flatten_multiple_appraisal_atom_2_1(self):
        appraisal_type = AppraisalType(name='Archival Appraisal')
        appraisal_type.save()

        appraisal_1 = Appraisal(
            metadata=self.metadata,
            appraisal_type=appraisal_type,
            appraisal_value='APPRAISAL 1',
            appraisal_note='NOTE 1'
        )
        appraisal_2 = Appraisal(
            metadata=self.metadata,
            appraisal_value='APPRAISAL 2',
        )
        appraisal_3 = Appraisal(
            metadata=self.metadata,
        )
        appraisal_1.save()
        appraisal_2.save()
        appraisal_3.save()

        flat = self.metadata.appraisals.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat['appraisal'], '* APPRAISAL 1. NOTE 1\n* APPRAISAL 2')

        appraisal_1.delete()
        appraisal_2.delete()
        appraisal_3.delete()
        appraisal_type.delete()


class TestAssociatedDocumentationManager(TestCase):
    ''' Testing manager for metadata.associated_documentation
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
        )
        doc_1.save()
        doc_2 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
        )
        doc_2.save()

        self.assertEqual(self.metadata.associated_documentation.count(), 2)

        doc_type.delete()
        doc_1.delete()
        doc_2.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.associated_documentation.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_doc_caais_1_0(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE',
            associated_documentation_note='NOTE',
        )
        doc_1.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['associatedDocumentationTypes'], 'Related Documentation')
        self.assertEqual(flat['associatedDocumentationTitles'], 'TITLE')
        self.assertEqual(flat['associatedDocumentationNotes'], 'NOTE')

        doc_1.delete()
        doc_type.delete()


    def test_flatten_multiple_doc_caais_1_0(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE 1',
            associated_documentation_note='NOTE 1',
        )
        doc_1.save()

        doc_2 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_title='TITLE 2',
        )
        doc_2.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['associatedDocumentationTypes'], 'Related Documentation|NULL')
        self.assertEqual(flat['associatedDocumentationTitles'], 'TITLE 1|TITLE 2')
        self.assertEqual(flat['associatedDocumentationNotes'], 'NOTE 1|NULL')

        doc_1.delete()
        doc_2.delete()
        doc_type.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_doc_atom_2_6(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE 1',
            associated_documentation_note='NOTE 1',
        )
        doc_1.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        doc_1.delete()
        doc_type.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_doc_atom_2_3(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE 1',
            associated_documentation_note='NOTE 1',
        )
        doc_1.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        doc_1.delete()
        doc_type.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_doc_atom_2_2(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE 1',
            associated_documentation_note='NOTE 1',
        )
        doc_1.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        doc_1.delete()
        doc_type.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_doc_atom_2_1(self):
        doc_type = AssociatedDocumentationType(name='Related Documentation')
        doc_type.save()

        doc_1 = AssociatedDocumentation(
            metadata=self.metadata,
            associated_documentation_type=doc_type,
            associated_documentation_title='TITLE 1',
            associated_documentation_note='NOTE 1',
        )
        doc_1.save()

        flat = self.metadata.associated_documentation.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        doc_1.delete()
        doc_type.delete()


class TestEventManager(TestCase):
    ''' Testing manager for metadata.events
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        event_1 = Event(metadata=self.metadata)
        event_2 = Event(metadata=self.metadata)
        event_3 = Event(metadata=self.metadata)
        event_1.save()
        event_2.save()
        event_3.save()

        self.assertEqual(self.metadata.events.count(), 3)

        event_1.delete()
        event_2.delete()
        event_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.events.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 3, 15, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_event_caais_1_0(self, timezone_now__patch):
        event_type = EventType(name='Updated')
        event_type.save()
        event_1 = Event(
            metadata=self.metadata,
            event_type=event_type,
            event_agent='AGENT 1',
            event_note='NOTE 1',
        )
        event_1.save()

        flat = self.metadata.events.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['eventTypes'], 'Updated')
        self.assertEqual(flat['eventDates'], '2023-03-15')
        self.assertEqual(flat['eventAgents'], 'AGENT 1')
        self.assertEqual(flat['eventNotes'], 'NOTE 1')

        event_1.delete()
        event_type.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_event_caais_1_0(self, timezone_now__patch):
        event_type = EventType(name='Updated')
        event_type.save()
        event_1 = Event(
            metadata=self.metadata,
            event_type=event_type,
            event_agent='AGENT 1',
            event_note='NOTE 1',
        )
        event_2 = Event(
            metadata=self.metadata
        )
        event_1.save()
        event_2.save()

        flat = self.metadata.events.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['eventTypes'], 'Updated|NULL')
        self.assertEqual(flat['eventDates'], '2023-02-28|2023-02-28')
        self.assertEqual(flat['eventAgents'], 'AGENT 1|NULL')
        self.assertEqual(flat['eventNotes'], 'NOTE 1|NULL')

        event_1.delete()
        event_2.delete()
        event_type.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_event_atom_2_6(self):
        # There are no events (as they are meant to be represented in CAAIS) in AtoM 2.6
        event_1 = Event(metadata=self.metadata)
        event_1.save()

        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        event_1.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_event_atom_2_3(self):
        # There are no events (as they are meant to be represented in CAAIS) in AtoM 2.3
        event_1 = Event(metadata=self.metadata)
        event_1.save()

        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        event_1.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_event_atom_2_2(self):
        # There are no events (as they are meant to be represented in CAAIS) in AtoM 2.2
        event_1 = Event(metadata=self.metadata)
        event_1.save()

        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        event_1.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_event_atom_2_1(self):
        # There are no events (as they are meant to be represented in CAAIS) in AtoM 2.1
        event_1 = Event(metadata=self.metadata)
        event_1.save()

        flat = self.metadata.events.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        event_1.delete()


class TestGeneralNoteManager(TestCase):
    ''' Testing manager for metadata.general_notes
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        general_note_1 = GeneralNote(metadata=self.metadata)
        general_note_2 = GeneralNote(metadata=self.metadata)
        general_note_3 = GeneralNote(metadata=self.metadata)
        general_note_1.save()
        general_note_2.save()
        general_note_3.save()

        self.assertEqual(self.metadata.general_notes.count(), 3)

        general_note_1.delete()
        general_note_2.delete()
        general_note_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.general_notes.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    def test_flatten_single_note_caais_1_0(self):
        note_1 = GeneralNote(
            metadata=self.metadata,
            general_note='NOTE 1'
        )
        note_1.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['generalNotes'], 'NOTE 1')

        note_1.delete()


    def test_flatten_multiple_note_caais_1_0(self):
        note_1 = GeneralNote(
            metadata=self.metadata,
            general_note='NOTE 1'
        )
        note_2 = GeneralNote(
            metadata=self.metadata,
            general_note='NOTE 2'
        )
        note_1.save()
        note_2.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['generalNotes'], 'NOTE 1|NOTE 2')

        note_1.delete()
        note_2.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    def test_flatten_single_note_atom_2_6(self):
        # There are no general notes in AtoM 2.6
        general_note_1 = GeneralNote(metadata=self.metadata)
        general_note_1.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_6)

        self.assertFalse(flat)

        general_note_1.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    def test_flatten_single_note_atom_2_3(self):
        # There are no general notes in AtoM 2.3
        general_note_1 = GeneralNote(metadata=self.metadata)
        general_note_1.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_3)

        self.assertFalse(flat)

        general_note_1.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_2)
        self.assertFalse(flat)


    def test_flatten_single_note_atom_2_2(self):
        # There are no general notes in AtoM 2.2
        general_note_1 = GeneralNote(metadata=self.metadata)
        general_note_1.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_2)

        self.assertFalse(flat)

        general_note_1.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    def test_flatten_single_note_atom_2_1(self):
        # There are no general notes in AtoM 2.1
        general_note_1 = GeneralNote(metadata=self.metadata)
        general_note_1.save()

        flat = self.metadata.general_notes.flatten(ExportVersion.ATOM_2_1)

        self.assertFalse(flat)

        general_note_1.delete()


class TestDateOfCreationOrRevisionManager(TestCase):
    ''' Testing manager for metadata.dates_of_creation_or_revision
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(name='Digital Transfer')
        cls.status, _ = Status.objects.get_or_create(name='Received')
        cls.metadata = Metadata(
            repository='Repository',
            accession_title='Title',
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials='2023-08-01',
            rules_or_conventions='CAAIS v1.0',
            language_of_accession_record='en'
        )
        cls.metadata.save()


    def test_access_related(self):
        date_1 = DateOfCreationOrRevision(metadata=self.metadata)
        date_2 = DateOfCreationOrRevision(metadata=self.metadata)
        date_3 = DateOfCreationOrRevision(metadata=self.metadata)
        date_1.save()
        date_2.save()
        date_3.save()

        self.assertEqual(self.metadata.dates_of_creation_or_revision.count(), 3)

        date_1.delete()
        date_2.delete()
        date_3.delete()


    def test_flatten_no_data_caais_1_0(self):
        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.CAAIS_1_0)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 9, 30, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_date_caais_1_0(self, timezone_now__patch):
        date_type = DateOfCreationOrRevisionType(name='Creation')
        date_type.save()

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_type=date_type,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_1.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['creationOrRevisionTypes'], 'Creation')
        self.assertEqual(flat['creationOrRevisionDates'], '2023-09-30')
        self.assertEqual(flat['creationOrRevisionAgents'], 'AGENT 1')
        self.assertEqual(flat['creationOrRevisionNotes'], 'NOTE 1')

        date_1.delete()
        date_type.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 5, 13, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_date_caais_1_0(self, timezone_now__patch):
        creation_type = DateOfCreationOrRevisionType(name='Creation')
        revision_type = DateOfCreationOrRevisionType(name='Revision')
        creation_type.save()
        revision_type.save()

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_type=creation_type,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_2 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_type=revision_type,
        )
        date_1.save()
        date_2.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat['creationOrRevisionTypes'], 'Creation|Revision')
        self.assertEqual(flat['creationOrRevisionDates'], '2023-05-13|2023-05-13')
        self.assertEqual(flat['creationOrRevisionAgents'], 'AGENT 1|NULL')
        self.assertEqual(flat['creationOrRevisionNotes'], 'NOTE 1|NULL')

        date_1.delete()
        date_2.delete()
        creation_type.delete()
        revision_type.delete()


    def test_flatten_no_data_atom_2_6(self):
        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_6)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 4, 18, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_date_atom_2_6(self, timezone_now__patch):
        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_1.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-04-18')

        date_1.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 10, 8, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_date_atom_2_6(self, timezone_now__patch):
        # Only the first date is taken

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_2 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 2',
            creation_or_revision_note='NOTE 2',
        )
        date_1.save()
        date_2.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-10-08')

        date_1.delete()
        date_2.delete()


    def test_flatten_no_data_atom_2_3(self):
        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 2, 3, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_date_atom_2_3(self, timezone_now__patch):
        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_1.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-02-03')

        date_1.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 7, 21, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_date_atom_2_3(self, timezone_now__patch):
        # Only the first date is taken

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_2 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 2',
            creation_or_revision_note='NOTE 2',
        )
        date_1.save()
        date_2.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-07-21')

        date_1.delete()
        date_2.delete()


    def test_flatten_no_data_atom_2_2(self):
        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_3)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 8, 20, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_date_atom_2_2(self, timezone_now__patch):
        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_1.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-08-20')

        date_1.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 5, 16, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_date_atom_2_2(self, timezone_now__patch):
        # Only the first date is taken

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_2 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 2',
            creation_or_revision_note='NOTE 2',
        )
        date_1.save()
        date_2.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-05-16')

        date_1.delete()
        date_2.delete()


    def test_flatten_no_data_atom_2_1(self):
        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_1)
        self.assertFalse(flat)


    @patch.object(timezone, 'now', return_value=datetime(2023, 9, 27, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_single_date_atom_2_1(self, timezone_now__patch):
        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_1.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-09-27')

        date_1.delete()


    @patch.object(timezone, 'now', return_value=datetime(2023, 6, 10, 12, 0, 0, tzinfo=timezone.get_current_timezone()))
    def test_flatten_multiple_date_atom_2_1(self, timezone_now__patch):
        # Only the first date is taken

        date_1 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 1',
            creation_or_revision_note='NOTE 1',
        )
        date_2 = DateOfCreationOrRevision(
            metadata=self.metadata,
            creation_or_revision_agent='AGENT 2',
            creation_or_revision_note='NOTE 2',
        )
        date_1.save()
        date_2.save()

        flat = self.metadata.dates_of_creation_or_revision.flatten(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(len(flat), 1)
        self.assertEqual(flat['acquisitionDate'], '2023-06-10')

        date_1.delete()
        date_2.delete()
