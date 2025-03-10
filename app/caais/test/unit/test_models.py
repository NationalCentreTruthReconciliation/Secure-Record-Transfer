from datetime import datetime

from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from caais.export import ExportVersion
from caais.models import (
    AcquisitionMethod,
    Appraisal,
    AppraisalType,
    ArchivalUnit,
    AssociatedDocumentation,
    CarrierType,
    ContentType,
    CreationOrRevisionType,
    DateOfCreationOrRevision,
    DispositionAuthority,
    EventType,
    Event,
    ExtentStatement,
    ExtentType,
    GeneralNote,
    Identifier,
    LanguageOfMaterial,
    Metadata,
    PreliminaryCustodialHistory,
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


class TestIdentifier(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquisition_method, _ = AcquisitionMethod.objects.get_or_create(
            name="Digital Transfer"
        )
        cls.status, _ = Status.objects.get_or_create(name="Received")
        cls.metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            acquisition_method=cls.acquisition_method,
            status=cls.status,
            date_of_materials="2023-08-01",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        cls.metadata.save()

    def test_new_identifier(self):
        identifier = Identifier(
            metadata=self.metadata,
            identifier_type="ID TYPE",
            identifier_value="ID VALUE",
            identifier_note="ID NOTE",
        )
        identifier.save()

        self.assertEqual(identifier.identifier_type, "ID TYPE")
        self.assertEqual(identifier.identifier_value, "ID VALUE")
        self.assertEqual(identifier.identifier_note, "ID NOTE")

        identifier.delete()

    def test_new_identifier_empty_note(self):
        identifier = Identifier(
            metadata=self.metadata,
            identifier_type="ID TYPE",
            identifier_value="ID VALUE",
        )
        identifier.save()

        self.assertEqual(identifier.identifier_type, "ID TYPE")
        self.assertEqual(identifier.identifier_value, "ID VALUE")
        self.assertEqual(identifier.identifier_note, "")

        identifier.delete()

    def test_new_identifier_empty_type(self):
        identifier = Identifier(metadata=self.metadata, identifier_value="ID VALUE")
        identifier.save()

        self.assertEqual(identifier.identifier_type, "")
        self.assertEqual(identifier.identifier_value, "ID VALUE")
        self.assertEqual(identifier.identifier_note, "")

    def test_new_identifier_raises_for_no_metadata(self):
        with self.assertRaises(IntegrityError):
            Identifier(identifier_value="VALUE").save()


class TestMetadata(TestCase):
    def test_new_metadata(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="2023-09-30",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        self.assertEqual(metadata.repository, "Repository")
        self.assertEqual(metadata.accession_title, "Title")
        self.assertEqual(metadata.date_of_materials, "2023-09-30")
        self.assertEqual(metadata.rules_or_conventions, "CAAIS v1.0")
        self.assertEqual(metadata.language_of_accession_record, "en")

    def test_flatten_metadata_no_related_caais_1_0(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="2023-09-30",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["repository"], "Repository")
        self.assertEqual(flat["accessionTitle"], "Title")
        self.assertEqual(flat["acquisitionMethod"], "")
        self.assertEqual(flat["status"], "")
        self.assertEqual(flat["dateOfMaterials"], "2023-09-30")
        self.assertEqual(flat["rulesOrConventions"], "CAAIS v1.0")
        self.assertEqual(flat["languageOfAccessionRecord"], "en")

        metadata.delete()

    def test_flatten_metadata_full_section_1_related_caais_1_0(self):
        """Test flattening of only section 1 of CAAIS metadata"""
        acquisition_method = AcquisitionMethod(name="Digital Transfer")
        status = Status(name="In Progress")
        metadata = Metadata(
            repository="My Repository",
            accession_title="Accession Title",
            acquisition_method=acquisition_method,
            status=status,
        )
        identifier_1 = Identifier(
            metadata=metadata,
            identifier_type="ID",
            identifier_value="111",
        )
        identifier_2 = Identifier(
            metadata=metadata, identifier_type="ID", identifier_note="Identifier to be received"
        )
        archival_unit_1 = ArchivalUnit(metadata=metadata, archival_unit="Unit 1")
        archival_unit_2 = ArchivalUnit(metadata=metadata, archival_unit="Unit 2")
        disposition_authority = DispositionAuthority(
            metadata=metadata, disposition_authority="Authority"
        )
        objects = (
            acquisition_method,
            status,
            metadata,
            identifier_1,
            identifier_2,
            archival_unit_1,
            archival_unit_2,
            disposition_authority,
        )
        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["repository"], "My Repository")
        self.assertEqual(flat["identifierTypes"], "ID|ID")
        self.assertEqual(flat["identifierValues"], "111|NULL")
        self.assertEqual(flat["identifierNotes"], "NULL|Identifier to be received")
        self.assertEqual(flat["accessionTitle"], "Accession Title")
        self.assertEqual(flat["archivalUnits"], "Unit 1|Unit 2")
        self.assertEqual(flat["dispositionAuthorities"], "Authority")
        self.assertEqual(flat["status"], "In Progress")

        for obj in objects:
            obj.delete()

    def test_flatten_metadata_full_section_2_related_caais_1_0(self):
        """Test flattening of only section 2 of CAAIS metadata"""
        metadata = Metadata()
        source_type, _ = SourceType.objects.get_or_create(name="Individual")
        source_role, _ = SourceRole.objects.get_or_create(name="Custodian")
        source_conf, _ = SourceConfidentiality.objects.get_or_create(name="Public")
        source = SourceOfMaterial(
            metadata=metadata,
            source_type=source_type,
            source_name="Name",
            contact_name="Contact Name",
            job_title="Title",
            organization="Org",
            phone_number="111 111-1111",
            email_address="user@example.com",
            address_line_1="123 3rd Street",
            address_line_2="Apt 3",
            city="Winnipeg",
            region="Manitoba",
            postal_or_zip_code="R4R 4R4",
            country="CA",
            source_role=source_role,
            source_note="Notes",
            source_confidentiality=source_conf,
        )
        history_1 = PreliminaryCustodialHistory(
            metadata=metadata,
            preliminary_custodial_history="History 1",
        )
        history_2 = PreliminaryCustodialHistory(
            metadata=metadata,
            preliminary_custodial_history="History 2",
        )
        objects = (metadata, source_type, source_role, source_conf, source, history_1, history_2)
        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["sourceType"], "Individual")
        self.assertEqual(flat["sourceName"], "Name")
        self.assertEqual(flat["sourceContactPerson"], "Contact Name")
        self.assertEqual(flat["sourceJobTitle"], "Title")
        self.assertEqual(flat["sourceOrganization"], "Org")
        self.assertEqual(flat["sourceStreetAddress"], "123 3rd Street, Apt 3")
        self.assertEqual(flat["sourceCity"], "Winnipeg")
        self.assertEqual(flat["sourceRegion"], "Manitoba")
        self.assertEqual(flat["sourcePostalCode"], "R4R 4R4")
        self.assertEqual(flat["sourceCountry"], "CA")
        self.assertEqual(flat["sourcePhoneNumber"], "111 111-1111")
        self.assertEqual(flat["sourceEmail"], "user@example.com")
        self.assertEqual(flat["sourceRole"], "Custodian")
        self.assertEqual(flat["sourceNote"], "Notes")
        self.assertEqual(flat["sourceConfidentiality"], "Public")
        self.assertEqual(flat["preliminaryCustodialHistory"], "History 1|History 2")

        for obj in objects:
            obj.delete()

    def test_flatten_metadata_full_section_3_related_caais_1_0(self):
        """Test flattening of only section 3 of CAAIS metadata"""
        metadata = Metadata(
            date_of_materials="Circa 2018",
        )
        extent_type = ExtentType(name="Extent Received")
        content_type = ContentType(name="Digital Content")
        carrier_type = CarrierType(name="Digital Transfer")
        extent_1 = ExtentStatement(
            metadata=metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure="10 PDF Files, worth 5MB",
            content_type=content_type,
            carrier_type=carrier_type,
        )
        extent_2 = ExtentStatement(
            metadata=metadata,
            quantity_and_unit_of_measure="1 XLSX file",
            content_type=content_type,
            extent_note="Notes",
        )
        language_1 = LanguageOfMaterial(
            metadata=metadata,
            language_of_material="English",
        )
        language_2 = LanguageOfMaterial(
            metadata=metadata,
            language_of_material="French",
        )
        objects = (
            metadata,
            extent_type,
            content_type,
            carrier_type,
            extent_1,
            extent_2,
            language_1,
            language_2,
        )
        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["dateOfMaterials"], "Circa 2018")
        self.assertEqual(flat["extentTypes"], "Extent Received|NULL")
        self.assertEqual(flat["quantityAndUnitOfMeasure"], "10 PDF Files, worth 5MB|1 XLSX file")
        self.assertEqual(flat["contentTypes"], "Digital Content|Digital Content")
        self.assertEqual(flat["carrierTypes"], "Digital Transfer|NULL")
        self.assertEqual(flat["extentNotes"], "NULL|Notes")
        self.assertEqual(flat["preliminaryScopeAndContent"], "")
        self.assertEqual(flat["languageOfMaterials"], "English|French")

        for obj in objects:
            obj.delete()

    @patch("django.conf.settings.APPROXIMATE_DATE_FORMAT", "Circa {date}")
    def test_flatten_metadata_full_section_3_related_caais_1_0_approximate_date(self):
        """Test flattening of only section 3 of CAAIS metadata, with the date of materials being
        approximate.
        """
        metadata = Metadata(
            date_of_materials="2018",
            date_is_approximate=True,
        )
        extent_type = ExtentType(name="Extent Received")
        content_type = ContentType(name="Digital Content")
        carrier_type = CarrierType(name="Digital Transfer")
        extent_1 = ExtentStatement(
            metadata=metadata,
            extent_type=extent_type,
            quantity_and_unit_of_measure="10 PDF Files, worth 5MB",
            content_type=content_type,
            carrier_type=carrier_type,
        )
        extent_2 = ExtentStatement(
            metadata=metadata,
            quantity_and_unit_of_measure="1 XLSX file",
            content_type=content_type,
            extent_note="Notes",
        )
        language_1 = LanguageOfMaterial(
            metadata=metadata,
            language_of_material="English",
        )
        language_2 = LanguageOfMaterial(
            metadata=metadata,
            language_of_material="French",
        )
        objects = (
            metadata,
            extent_type,
            content_type,
            carrier_type,
            extent_1,
            extent_2,
            language_1,
            language_2,
        )
        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["dateOfMaterials"], "Circa 2018")
        self.assertEqual(flat["extentTypes"], "Extent Received|NULL")
        self.assertEqual(flat["quantityAndUnitOfMeasure"], "10 PDF Files, worth 5MB|1 XLSX file")
        self.assertEqual(flat["contentTypes"], "Digital Content|Digital Content")
        self.assertEqual(flat["carrierTypes"], "Digital Transfer|NULL")
        self.assertEqual(flat["extentNotes"], "NULL|Notes")
        self.assertEqual(flat["preliminaryScopeAndContent"], "")
        self.assertEqual(flat["languageOfMaterials"], "English|French")

        for obj in objects:
            obj.delete()

    def test_flatten_metadata_full_section_4_related_caais_1_0(self):
        metadata = Metadata()
        location_1 = StorageLocation(
            metadata=metadata,
            storage_location="DPAS",
        )
        location_2 = StorageLocation(
            metadata=metadata,
            storage_location="External Hard Drive A",
        )
        rights_type = RightsType(
            name="Public Domain",
        )
        rights = Rights(
            metadata=metadata,
            rights_type=rights_type,
            rights_value="All records in the public domain",
        )
        req_type = PreservationRequirementsType(
            name="Digital Preservation",
            description="Backups and fixity needed to verify digital material",
        )
        preservation_requirement = PreservationRequirements(
            metadata=metadata,
            preservation_requirements_type=req_type,
            preservation_requirements_value="Handle in accordance with other digital material",
        )
        appraisal_type = AppraisalType(name="Archival Appraisal")
        appraisal_1 = Appraisal(
            metadata=metadata,
            appraisal_type=appraisal_type,
            appraisal_value="9/10 PDF files are of archival value",
            appraisal_note="PDF file that is not relevant is named letter.pdf",
        )
        appraisal_2 = Appraisal(
            metadata=metadata,
            appraisal_type=appraisal_type,
            appraisal_value="1 XLSX file is archivally relevant",
        )
        documentation_1 = AssociatedDocumentation(
            metadata=metadata,
            associated_documentation_title="Records Submission, 2023",
            associated_documentation_note="Subject line of email sent to repository prior to submission",
        )

        objects = (
            metadata,
            location_1,
            location_2,
            rights_type,
            rights,
            req_type,
            preservation_requirement,
            appraisal_type,
            appraisal_1,
            appraisal_2,
            documentation_1,
        )

        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["storageLocation"], "DPAS|External Hard Drive A")
        self.assertEqual(flat["rightsTypes"], "Public Domain")
        self.assertEqual(flat["rightsValues"], "All records in the public domain")
        self.assertEqual(flat["rightsNotes"], "NULL")
        self.assertEqual(flat["preservationRequirementsTypes"], "Digital Preservation")
        self.assertEqual(
            flat["preservationRequirementsValues"],
            "Handle in accordance with other digital material",
        )
        self.assertEqual(flat["preservationRequirementsNotes"], "NULL")
        self.assertEqual(flat["appraisalTypes"], "Archival Appraisal|Archival Appraisal")
        self.assertEqual(
            flat["appraisalValues"],
            "9/10 PDF files are of archival value|1 XLSX file is archivally relevant",
        )
        self.assertEqual(
            flat["appraisalNotes"], "PDF file that is not relevant is named letter.pdf|NULL"
        )
        self.assertEqual(flat["associatedDocumentationTypes"], "NULL")
        self.assertEqual(flat["associatedDocumentationTitles"], "Records Submission, 2023")
        self.assertEqual(
            flat["associatedDocumentationNotes"],
            "Subject line of email sent to repository prior to submission",
        )

        for obj in objects:
            obj.delete()

    @patch.object(
        timezone,
        "now",
        return_value=datetime(2023, 12, 5, 12, 0, 0, tzinfo=timezone.get_current_timezone()),
    )
    def test_flatten_metadata_full_section_5_related_caais_1_0(self, timezone_now__patch):
        metadata = Metadata()
        event_type_1 = EventType(name="Metadata Received")
        event_type_2 = EventType(name="Files Received")
        event_1 = Event(
            metadata=metadata,
            event_type=event_type_1,
            event_agent="Transfer application",
        )
        event_2 = Event(
            metadata=metadata,
            event_type=event_type_2,
            event_agent="Submitter",
            event_note="Files submitted using a separate mechanism",
        )
        objects = (metadata, event_type_1, event_type_2, event_1, event_2)
        for obj in objects:
            obj.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["eventTypes"], "Metadata Received|Files Received")
        self.assertEqual(flat["eventDates"], "2023-12-05|2023-12-05")
        self.assertEqual(flat["eventAgents"], "Transfer application|Submitter")
        self.assertEqual(flat["eventNotes"], "NULL|Files submitted using a separate mechanism")

        for obj in objects:
            obj.delete()

    def test_flatten_metadata_full_section_6_related_caais_1_0(self):
        metadata = Metadata()
        note_1 = GeneralNote(
            metadata=metadata,
            general_note="Note 1",
        )
        note_2 = GeneralNote(
            metadata=metadata,
            general_note="Note 2",
        )
        note_3 = GeneralNote(
            metadata=metadata,
            general_note="Note 3",
        )
        metadata.save()
        note_1.save()
        note_2.save()
        note_3.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["generalNotes"], "Note 1|Note 2|Note 3")

        note_1.delete()
        note_2.delete()
        note_3.delete()
        metadata.delete()

    @patch.object(
        timezone,
        "now",
        return_value=datetime(2023, 5, 23, 12, 0, 0, tzinfo=timezone.get_current_timezone()),
    )
    def test_flatten_metadata_full_section_7_caais_1_0(self, timezone_now__patch):
        metadata = Metadata(
            rules_or_conventions="CAAIS 1.0",
            language_of_accession_record="en",
        )
        creation_type, ct_created = CreationOrRevisionType.objects.get_or_create(name="Created")
        revision_type, rt_created = CreationOrRevisionType.objects.get_or_create(name="Revised")
        date_1 = DateOfCreationOrRevision(
            metadata=metadata,
            creation_or_revision_type=creation_type,
            creation_or_revision_agent="Transfer application",
        )
        date_2 = DateOfCreationOrRevision(
            metadata=metadata,
            creation_or_revision_type=revision_type,
            creation_or_revision_agent="Transfer application",
            creation_or_revision_note="Revised to meet repository standards",
        )

        metadata.save()
        date_1.save()
        date_2.save()

        flat = metadata.create_flat_representation(ExportVersion.CAAIS_1_0)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.CAAIS_1_0.fieldnames)

        self.assertEqual(flat["rulesOrConventions"], "CAAIS 1.0")
        self.assertEqual(flat["creationOrRevisionTypes"], "Created|Revised")
        self.assertEqual(flat["creationOrRevisionDates"], "2023-05-23|2023-05-23")
        self.assertEqual(
            flat["creationOrRevisionAgents"], "Transfer application|Transfer application"
        )
        self.assertEqual(
            flat["creationOrRevisionNotes"], "NULL|Revised to meet repository standards"
        )
        self.assertEqual(flat["languageOfAccessionRecord"], "en")

        date_1.delete()
        date_2.delete()
        if ct_created:
            creation_type.delete()
        if rt_created:
            revision_type.delete()
        metadata.delete()

    def test_flatten_metadata_no_related_atom_2_6(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="September 2023",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        flat = metadata.create_flat_representation(ExportVersion.ATOM_2_6)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_6.fieldnames)

        self.assertEqual(flat["title"], "Title")
        self.assertEqual(flat["acquisitionType"], "")
        self.assertEqual(flat["eventTypes"], "Creation")
        self.assertEqual(flat["eventDates"], "September 2023")
        self.assertEqual(flat["eventStartDates"], "2023-09-01")
        self.assertEqual(flat["eventEndDates"], "2023-09-30")

        metadata.delete()

    def test_flatten_metadata_no_related_atom_2_3(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="June 2023",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        flat = metadata.create_flat_representation(ExportVersion.ATOM_2_3)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_3.fieldnames)

        self.assertEqual(flat["title"], "Title")
        self.assertEqual(flat["acquisitionType"], "")
        self.assertEqual(flat["eventTypes"], "Creation")
        self.assertEqual(flat["eventDates"], "June 2023")
        self.assertEqual(flat["eventStartDates"], "2023-06-01")
        self.assertEqual(flat["eventEndDates"], "2023-06-30")

        metadata.delete()

    def test_flatten_metadata_no_related_atom_2_2(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="[ca. 2018]",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        flat = metadata.create_flat_representation(ExportVersion.ATOM_2_2)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_2.fieldnames)

        self.assertEqual(flat["title"], "Title")
        self.assertEqual(flat["acquisitionType"], "")
        self.assertEqual(flat["creationDatesType"], "Creation")
        self.assertEqual(flat["creationDates"], "2018")
        self.assertEqual(flat["creationDatesStart"], "2018-01-01")
        self.assertEqual(flat["creationDatesEnd"], "2018-12-31")

        metadata.delete()

    def test_flatten_metadata_no_related_atom_2_1(self):
        metadata = Metadata(
            repository="Repository",
            accession_title="Title",
            date_of_materials="2020-12-00",
            rules_or_conventions="CAAIS v1.0",
            language_of_accession_record="en",
        )
        metadata.save()

        flat = metadata.create_flat_representation(ExportVersion.ATOM_2_1)

        # Assure no weird keys were added
        for key in flat.keys():
            self.assertIn(key, ExportVersion.ATOM_2_1.fieldnames)

        self.assertEqual(flat["title"], "Title")
        self.assertEqual(flat["acquisitionType"], "")

        metadata.delete()
