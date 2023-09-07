''' Models describing the Canadian Archival Accession Information Standard v1.0:

https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf

Note that there are **seven** sections of CAAIS that organize the fields by
related information. These sections are:

1. Identity Information Section
2. Source Information Section
3. Materials Information Section
4. Management Information Section
5. Event Information Section
6. General Information Section
7. Control Information Section

The models here are not in the exact *order* as in the CAAIS document, but each
field in the standard is defined in a model.
'''
from abc import ABC, abstractmethod
from functools import partial

from django.conf import settings
from django.db import models
from django.db.models import Q, CharField, Value, Case, When, Value, F
from django.db.models.functions import Coalesce, Concat
from django.utils.translation import gettext, gettext_lazy as _
from django_countries.fields import CountryField

from caais.dates import EventDateParser, UnknownDateFormat
from caais.db import DefaultConcat
from caais.export import ExportVersion



class CaaisModelManager(models.Manager, ABC):
    ''' Custom manager for CAAIS models that require the flatten() function.
    '''

    @abstractmethod
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Flatten metadata to be used for AtoM
        '''
        if version in (
                ExportVersion.CAAIS_1_0,
            ):
            raise ValueError(f'{version} is not an AtoM version')

    @abstractmethod
    def flatten_caais(self, version: ExportVersion) -> dict:
        ''' Flatten metadata to be used for CAAIS
        '''
        if version not in (
                ExportVersion.CAAIS_1_0,
            ):
            raise ValueError(f'{version} is not a CAAIS version')

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0) -> dict:
        ''' Flatten metadata to be used in BagIt metadata or CSV file
        '''
        if version == ExportVersion.CAAIS_1_0:
            self.flatten_caais(version)
        else:
            self.flatten_atom(version)



class TermManager(models.Manager):
    ''' Custom manager for terms that excludes all empty or NULL terms from
    queryset.
    '''

    def get_queryset(self):
        ''' Returns all terms that havea a name.
        '''
        return super().get_queryset().exclude(
            Q(name__iexact='') | Q(name__isnull=True)
        )


class AbstractTerm(models.Model):
    ''' An abstract class that can be used to define any term that consists of
    a name and a description.

    Attributes:
        name (CharField): The name of the term. Terms must have unique names
        description (TextField): A description for the term
    '''

    class Meta:
        abstract = True

    name = models.CharField(max_length=128, null=False, blank=False, unique=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


class Status(AbstractTerm):
    ''' 1.7 Status (Non-repeatable)

    The current position of the material with respect to the repository's
    workflows and business processes.
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Statuses')
        verbose_name = gettext('Status')
Status._meta.get_field('name').help_text = gettext(
    "Record the current position of the material with respect to the "
    "repository's workflows and business processes using a controlled "
    "vocabulary"
)


class MetadataManager(models.Manager):
    ''' Custom metadata manager that provides a function to flatten metadata
    objects to be able to write them to a CSV.
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten metadata objects in queryset to be exported as CSV rows.
        '''
        return [
            metadata.flatten(version) for metadata in self.get_queryset().all()
        ]


class Metadata(models.Model):
    ''' Top-level container for all CAAIS metadata. Contains all simple
    non-repeatable fields. Any repeatable field is represented by a separate
    model with a ForeignKey.
    '''

    class Meta:
        verbose_name_plural = gettext('CAAIS metadata')
        verbose_name = gettext('CAAIS metadata')

    objects = MetadataManager()

    # 1.1 Repository
    # The name of the institution that accepts legal responsibility for the
    # accessioned material.
    repository = models.CharField(max_length=128, null=True, help_text=gettext(
        "Give the authorized form(s) of the name of the institution in "
        "accordance with the repository's naming standard"
    ))

    # 1.2 Identifiers
    # See: Identifier model. Accessible via related with self.identifiers

    # 1.3 Accession Title
    # The name assigned to the material.
    accession_title = models.CharField(max_length=128, null=True, help_text=gettext(
        "Supply an accession title in accordance with the repository's "
        "descriptive standard, typically consisting of the creator's name(s) "
        "and the type of material"
    ))

    # 1.4 Archival Unit
    # See: ArchivalUnit model. Accessible via related with self.archival_units

    # 1.5 Acquisition Method
    # The process by which a repository acquires material.
    acquisition_method = models.CharField(max_length=128, null=True, help_text=gettext(
        "Record the acquisition method in accordance with a controlled "
        "vocabulary"
    ))

    # 1.6 Disposition Authority
    # See: DispositionAuthority model. Accessible via related with
    # self.disposition_authorities

    # 1.7 Status
    # The current position of the material with respect to the repository's
    # workflows and business processes.
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)

    # 2.1 Source of Material
    # See: SourceOfMaterial model. Accessible via related with
    # self.source_of_materials

    # 2.2 Preliminary Custodial History
    # See: PreliminaryCustodialHistory model. Accessible via related with
    # self.preliminary_custodial_histories

    # 3.1 Date of Material
    # A date or date range indicating when the materials were known or thought
    # to have been created.
    date_of_material = models.CharField(max_length=128, null=True, help_text=gettext(
        "Provide a preliminary estimate of the date range or explicitly "
        "indicate if not it has yet been determined"
    ))

    # 3.2 Extent Statement
    # See: ExtentStatement model. Accessible via related with
    # self.extent_statements

    # 3.3 Preliminary Scope and Content
    # See: PreliminaryScopeAndContent model. Accessible via related with
    # self.preliminary_scope_and_contents

    # 7.1 Rules or Conventions
    # The rules, conventions or templates that were used in creating or
    # maintaining the accession record.
    rules_or_conventions = models.CharField(max_length=255, blank=True, default='', help_text=gettext(
        "Record information about the standards, rules or conventions that were followed when creating or maintaining "
        "the accession record. Indicate the software application if the accession record is based on a data entry "
        "template in a database or other automated system. Give the version number of the standard or software "
        "application where applicable."
    ))

    # 7.2 Date of Creation or Revision
    # See: DateOfCreationOrRevision model. Accessible via related with
    # self.date_of_creation_or_revisions

    # 7.3 Language of Accession record
    # The language(s) and script(s) used to record information in the accession
    # record.
    language_of_accession_record = models.CharField(max_length=20, blank=True, default='en', help_text=gettext(
        "Record the language(s) and script(s) used to create the accession record. If the content has been translated "
        "and is available in other languages, give those languages. Provide information about script only where it is "
        "common to use multiple scripts to represent a language and it is important to know which script is employed."
    ))

    #pylint: disable=no-member
    def flatten(self, version=ExportVersion.CAAIS_1_0) -> dict:
        ''' Convert this model and all related models into a flat dictionary
        suitable to be written to a CSV or used as the metadata fields for a
        BagIt bag.
        '''

        row = {c: '' for c in version.fieldnames}

        if version == ExportVersion.CAAIS_1_0:
            row['repository'] = self.repository or ''
            row['accessionTitle'] = self.accession_title or 'No title'
            row['acquisitionMethod'] = self.acquisition_method or ''
            row['dateOfMaterial'] = self.date_of_material or ''
            row['rulesOrConventions'] = self.rules_or_conventions or ''
            row['levelOfDetail'] = self.LevelOfDetail(self.level_of_detail).label or ''
            row.update(self.language_of_materials.flatten(version))
            row['languageOfAccessionRecord'] = self.language_of_accession_record or ''
        else:
            row['title'] = self.accession_title or 'No title'
            row['acquisitionType'] = self.acquisition_method or ''

            row['accessionNumber'] = self.identifiers.accession_identifier().identifier_value if \
                self.identifiers.accession_identifier() is not None else ''

            if self.date_of_material:
                try:
                    parser = EventDateParser(
                        unknown_date=settings.CAAIS_UNKNOWN_DATE_TEXT,
                        unknown_start_date=settings.CAAIS_UNKNOWN_START_DATE,
                        unknown_end_date=settings.CAAIS_UNKNOWN_END_DATE,
                        timid=False
                    )
                    parsed_date, date_range = parser.parse_date(self.date_of_material)
                    if len(date_range) == 1:
                        start_date, end_date = date_range[0], date_range[0]
                    else:
                        start_date, end_date = date_range[0], date_range[1]

                    if version in (ExportVersion.ATOM_2_1, ExportVersion.ATOM_2_2):
                        row['creationDatesType'] = 'Creation'
                        row['creationDates'] = parsed_date
                        row['creationDatesStart'] = str(start_date)
                        row['creationDatesEnd'] = str(end_date)
                    else:
                        row['eventTypes'] = 'Creation'
                        row['eventDates'] = parsed_date
                        row['eventStartDates'] = str(start_date)
                        row['eventEndDates'] = str(end_date)
                except UnknownDateFormat:
                    if version in (ExportVersion.ATOM_2_1, ExportVersion.ATOM_2_2):
                        row['creationDatesType'] = 'Creation'
                        row['creationDates'] = settings.CAAIS_UNKNOWN_DATE_TEXT
                        row['creationDatesStart'] = settings.CAAIS_UNKNOWN_START_DATE
                        row['creationDatesEnd'] = settings.CAAIS_UNKNOWN_END_DATE
                    else:
                        row['eventTypes'] = 'Creation'
                        row['eventDates'] = settings.CAAIS_UNKNOWN_DATE_TEXT
                        row['eventStartDates'] = settings.CAAIS_UNKNOWN_START_DATE
                        row['eventEndDates'] = settings.CAAIS_UNKNOWN_END_DATE
            language_updates = self.language_of_materials.flatten(version)
            if language_updates or self.scope_and_content:
                combined_updates = {
                    'scopeAndContent': '. '.join([
                        self.scope_and_content.rstrip('. '),
                        language_updates['scopeAndContent'].rstrip('. '),
                    ])
                }
                row.update(combined_updates)
            row['archivalHistory'] = self.custodial_history

        row.update(self.identifiers.flatten(version))
        row.update(self.archival_units.flatten(version))
        row.update(self.source_of_materials.flatten(version))
        row.update(self.extent_statements.flatten(version))
        row.update(self.storage_locations.flatten(version))
        row.update(self.rights.flatten(version))
        row.update(self.material_assessments.flatten(version))
        row.update(self.events.flatten(version))
        row.update(self.general_notes.flatten(version))
        row.update(self.date_creation_revisions.flatten(version))
        return row

    def __str__(self):
        return self.accession_title or 'No title'

    def update_accession_id(self, accession_id: str, commit: bool = True):
        a_id = self.identifiers.accession_identifier()
        if a_id is not None:
            a_id.identifier_value = accession_id
            if commit:
                a_id.save()


class IdentifierManager(CaaisModelManager):
    ''' Custom manager for identifiers
    '''

    def accession_identifier(self):
        ''' Get the first identifier with Accession Identifier or Accession
        Number as the type, or None if an identifier like this does not exist.
        '''
        return self.get_queryset().filter(
            Q(identifier_type__icontains='Accession Identifier') |
            Q(identifier_type__icontains='Accession Number')
        ).first()

    def flatten_atom(self, version) -> dict:
        super().flatten_atom(version)

        # alternativeIdentifiers were added in AtoM v2.6
        if version in (ExportVersion.ATOM_2_1, ExportVersion.ATOM_2_2, ExportVersion.ATOM_2_3):
            return {}

        return self.get_queryset().filter(
            Q(identifier_type__icontains='Accession Identifier', _negated=True) &
            Q(identifier_type__icontains='Accession Number', _negated=True)
        ).aggregate(
            alternativeIdentifiers=DefaultConcat(
                Coalesce('identifier_value', Value('NULL')),
            ),
            alternativeIdentifierTypes=DefaultConcat(
                Coalesce('identifier_type', Value('NULL')),
            ),
            alternativeIdentifierNotes=DefaultConcat(
                Coalesce('identifier_note', Value('NULL')),
            )
        )

    def flatten_caais(self, version) -> dict:
        super().flatten_caais(version)
        return self.get_queryset().aggregate(
            identifierTypes=DefaultConcat(
                Coalesce('identifier_type', Value('NULL'))
            ),
            identifierValues=DefaultConcat(
                Coalesce('identifier_value', Value('NULL'))
            ),
            identifierNotes=DefaultConcat(
                Coalesce('identifier_note', Value('NULL'))
            ),
        )


class Identifier(models.Model):
    ''' 1.2 Identifiers (Repeatable field - One Mandatory)

    Alphabetic, numeric, or alpha-numeric codes assigned to accessioned
    material, parts of the material, or accruals for purposes of unique for
    purposes of identification.
    '''

    objects = IdentifierManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='identifiers')

    # 1.2.1 Identifier Type
    # A term or phrase that characterizes the nature of the identifier.
    identifier_type = models.CharField(max_length=128, null=False, help_text=gettext(
        "Record the identifier type in accordance with a controlled vocabulary "
        "maintained by the repository"
    ))

    # 1.2.2 Identifier Value
    # A code that is assigned to the material to support identification in the
    # course of processes and activities such as acquisition, transfer, ingest,
    # and conservation.
    identifier_value = models.CharField(max_length=128, null=False, help_text=gettext(
        "Record the other identifier value as received or generated by the "
        "repository"
    ))

    # 1.2.3 Identifier Note
    # Additional information about the identifier, including contextual
    # information on the purpose of the identifier.
    identifier_note = models.TextField(null=True, help_text=gettext(
        "Record any additional information that clarifies the purpose, use or "
        "generation of the identifier."
    ))

    def __str__(self):
        return f'{self.identifier_value} ({self.identifier_type})'


class ArchivalUnitManager(CaaisModelManager):
    ''' Custom archival unit manager
    '''

    def flatten_atom(self, version: ExportVersion) -> dict:
        super().flatten_atom(version)
        # No equivalent for archival unit in AtoM
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        super().flatten_caais(version)
        # Don't bother including NULL for empty archival units, just skip them
        return self.get_queryset().exclude(
            Q(archival_unit__exact='') |
            Q(archival_unit__isnull=True)
        ).aggregate(
            archivalUnits=DefaultConcat('archival_unit')
        )


class ArchivalUnit(models.Model):
    ''' 1.4 Archival Unit (Repeatable field - Optional)

    The archival unit or the aggregate to which the accessioned material
    belongs.
    '''

    objects = ArchivalUnitManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='archival_units')

    archival_unit = models.TextField(null=False, help_text=gettext(
        "Record the reference code and/or title of the archival unit to which "
        "the accession belongs"
    ))

    def __str__(self):
        return f'Archival Unit #{self.id}'


class DispositionAuthorityManager(CaaisModelManager):
    ''' Custom disposition authority manager
    '''

    def flatten_atom(self, version: ExportVersion) -> dict:
        super().flatten_atom(version)
        # No equivalent for disposition authority in AtoM
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        ''' Flatten disposition authorities in queryset to export them in a CSV.
        '''
        super().flatten_caais(version)
        # Don't bother including NULL for empty disposition authority, just skip it
        return self.get_queryset().exclude(
            Q(disposition_authority__exact='') |
            Q(disposition_authority__isnull=True)
        ).aggregate(
            dispositionAuthority=DefaultConcat('disposition_authority')
        )


class DispositionAuthority(models.Model):
    ''' 1.6 - Disposition Authority (Repeatable field)

    A reference to policies, directives, and agreements that prescribe and allow
    for the transfer of material to a repository.
    '''

    class Meta:
        verbose_name_plural = gettext('Disposition authorities')
        verbose_name = gettext('Disposition authority')

    objects = DispositionAuthorityManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='disposition_authorities')

    disposition_authority = models.TextField(null=False, help_text=gettext(
        "Record information about any legal instruments that apply to the "
        "accessioned material. Legal instruments include statutes, records "
        "schedules or disposition authorities, and donor agreements"
    ))

    def __str__(self):
        return f'Disposition Authority #{self.id}'


class SourceType(AbstractTerm):
    ''' 2.1.1 Source Type (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source types')
        verbose_name = gettext('Source type')
SourceType._meta.get_field('name').help_text = gettext(
    "Record the source in accordance with a controlled vocabulary maintained "
    "by the repository"
)


class SourceRole(AbstractTerm):
    ''' 2.1.4 Source Role (Non-repeatable)

    The relationship of the named source to the material.
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source roles')
        verbose_name = gettext('Source role')
SourceRole._meta.get_field('name').help_text = gettext(
    "Record the source role (when known) in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class SourceConfidentiality(AbstractTerm):
    ''' 2.1.6 Source Confidentiality

    An instruction to maintain information about the source in confidence.
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source confidentialities')
        verbose_name = gettext('Source confidentiality')
SourceConfidentiality._meta.get_field('name').help_text = gettext(
    "Record source statements or source information that is for internal use "
    "only by the repository. Repositories should develop a controlled "
    "vocabulary with terms that can be translated into clear rules for "
    "handling source information"
)


class SourceOfMaterialManager(CaaisModelManager):
    ''' Custom source of material manager
    '''

    def flatten_atom(self, version: ExportVersion) -> dict:
        super().flatten_atom(version)
        # AtoM only supports one "donor"
        first_donor = self.get_queryset().order_by('id').first()

        address = ', '.join(l for l in [
            first_donor.address_line_1,
            first_donor.address_line_2,
        ] if l)

        flat = {
            'donorName': first_donor.source_name or '',
            'donorStreetAddress': address,
            'donorCity': first_donor.city or '',
            'donorRegion': first_donor.region or '',
            'donorPostalCode': first_donor.postal_code or '',
            'donorCountry': first_donor.country.code or '',
            'donorTelephone': first_donor.phone_number or '',
            'donorEmail': first_donor.email or '',
        }

        # donorNote added in AtoM 2.6
        # donorContactPerson added in AtoM 2.6
        if version == ExportVersion.ATOM_2_6:
            flat['donorContactPerson'] = first_donor.contact_name

            note = first_donor.source_note
            role = first_donor.source_role.name
            type_ = first_donor.source_type.name
            confidentiality = first_donor.source_confidentiality

            # Create narrative for donor note
            if any(note, role, type_, confidentiality):
                donor_narrative = []
                if type_:
                    if type_[0].lower() in ('a', 'e', 'i', 'o', 'u'):
                        donor_narrative.append(f'The donor is an {type_}')
                    else:
                        donor_narrative.append(f'The donor is a {type_}')
                if role:
                    donor_narrative.append(
                        f"The donor's relationship to the records is: {role}"
                    )
                if confidentiality:
                    donor_narrative.append(
                        f'The donor\'s confidentiality has been noted as: {confidentiality}'
                    )
                if note:
                    donor_narrative.append(note)

                flat['donorNote'] = '. '.join(donor_narrative)

        return flat

    def flatten_caais(self, version: ExportVersion) -> dict:
        ''' Flatten source of material info in queryset to export them in a CSV.
        '''
        super().flatten_caais(version)
        queryset = self.get_queryset()
        return {
            # Countries don't behave in the query, so concatenate them separately
            'sourceCountry': '|'.join([x.country.code for x in queryset]),
            **queryset.annotate(
                # Coalesce addresses to empty strings make case logic simpler
                clean_address_line_1=Coalesce('address_line_1', Value('')),
                clean_address_line_2=Coalesce('address_line_2', Value('')),
            ).annotate(
                # Add joined address field to query
                address=Case(
                    When(Q(clean_address_line_1='') & Q(clean_address_line_2=''), then=Value('NULL')),
                    When(Q(clean_address_line_1=''), then=F('clean_address_line_2')),
                    When(Q(clean_address_line_2=''), then=F('clean_address_line_1')),
                    default=Concat(F('clean_address_line_1'), Value(', '), F('clean_address_line_2')),
                    output_field=CharField(),
                )
            ).aggregate(
                sourceType=DefaultConcat(Case(
                    When((Q(source_type__name='') | Q(source_type__name__isnull=True)),
                        then=Value('NULL')),
                    default=F('source_type__name'),
                    output_field=CharField(),
                )),
                sourceName=DefaultConcat(Case(
                    When((Q(source_name='') | Q(source_name__isnull=True)),
                            then=Value('NULL')),
                    default=F('source_name'),
                    output_field=CharField(),
                )),
                sourceContactPerson=DefaultConcat(Case(
                    When((Q(contact_name='') | Q(contact_name__isnull=True)),
                            then=Value('NULL')),
                    default=F('contact_name'),
                    output_field=CharField(),
                )),
                sourceJobTitle=DefaultConcat(Case(
                    When((Q(job_title='') | Q(job_title__isnull=True)),
                            then=Value('NULL')),
                    default=F('job_title'),
                    output_field=CharField(),
                )),
                sourceStreetAddress=DefaultConcat('address'), # Address is already sanitized
                sourceCity=DefaultConcat(Case(
                    When((Q(city='') | Q(city__isnull=True)),
                            then=Value('NULL')),
                    default=F('city'),
                    output_field=CharField(),
                )),
                sourceRegion=DefaultConcat(Case(
                    When((Q(region='') | Q(region__isnull=True)),
                            then=Value('NULL')),
                    default=F('region'),
                    output_field=CharField(),
                )),
                sourcePostalCode=DefaultConcat(Case(
                    When((Q(postal_or_zip_code='') | Q(postal_or_zip_code__isnull=True)),
                            then=Value('NULL')),
                    default=F('postal_or_zip_code'),
                    output_field=CharField(),
                )),
                sourcePhoneNumber=DefaultConcat(Case(
                    When((Q(phone_number='') | Q(phone_number__isnull=True)),
                            then=Value('NULL')),
                    default=F('phone_number'),
                    output_field=CharField(),
                )),
                sourceEmail=DefaultConcat(Case(
                    When((Q(email_address='') | Q(email_address__isnull=True)),
                            then=Value('NULL')),
                    default=F('email_address'),
                    output_field=CharField(),
                )),
                sourceRole=DefaultConcat(Case(
                    When((Q(source_role__name='') | Q(source_role__name__isnull=True)),
                            then=Value('NULL')),
                    default=F('source_role__name'),
                    output_field=CharField(),
                )),
                sourceNote=DefaultConcat(Case(
                    When((Q(source_note='') | Q(source_note__isnull=True)),
                            then=Value('NULL')),
                    default=F('source_note'),
                    output_field=CharField(),
                )),
                sourceConfidentiality=DefaultConcat(Case(
                    When((Q(source_confidentiality__name='') | Q(source_confidentiality__name__isnull=True)),
                            then=Value('NULL')),
                    default=F('source_confidentiality__name'),
                    output_field=CharField(),
                )),
            )
        }


class SourceOfMaterial(models.Model):
    ''' 2.1 Source of Material (Repeatable - One Mandatory)

    A corporate body, person or family responsible for the creation, use or
    transfer of the accessioned material.
    '''

    class Meta:
        verbose_name_plural = gettext('Sources of material')
        verbose_name = gettext('Source of material')

    objects = SourceOfMaterialManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='source_of_materials')

    # 2.1.1 Source Type
    # A term describing the nature of the source.
    source_type = models.ForeignKey(SourceType, on_delete=models.SET_NULL,
                                    null=True, related_name='source_of_materials')

    # 2.1.2 Source Name
    # The proper name of the source of the material.
    source_name = models.CharField(max_length=256, null=False, default='', help_text=gettext(
        "Record the source name in accordance with the repository's "
        "descriptive standard"
    ))

    # 2.1.3 Source Contact Information
    # Multiple fields represent this one field
    contact_name = models.CharField(max_length=256, blank=True, default='')
    job_title = models.CharField(max_length=256, blank=True, default='')
    phone_number = models.CharField(max_length=32, null=False)
    email_address = models.CharField(max_length=256, null=False)
    address_line_1 = models.CharField(max_length=256, blank=True, default='')
    address_line_2 = models.CharField(max_length=256, blank=True, default='')
    city = models.CharField(max_length=128, blank=True, default='')
    region = models.CharField(max_length=128, blank=True, default='')
    postal_or_zip_code = models.CharField(max_length=16, blank=True, default='')
    country = CountryField(null=True)

    # 2.1.4 Source Role
    source_role = models.ForeignKey(SourceRole, on_delete=models.SET_NULL,
                                    null=True, related_name='source_of_materials')

    # 2.1.5 Source Note
    # An open element to capture any additional information about the source, or
    # circumstances surrounding their role.
    source_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information about the source of the accessioned "
        "materials. If the source performed the role for only a specific "
        "period of time (e.g. was a custodian for several years), record the "
        "dates in this element"
    ))

    # 2.1.6 Source Confidentiality
    source_confidentiality = models.ForeignKey(SourceConfidentiality, on_delete=models.SET_NULL,
                                               null=True, related_name='source_of_materials')

    def __str__(self):
        return f'{self.source_name} (Phone: {self.phone_number})'


class PreliminaryCustodialHistoryManager(CaaisModelManager):
    ''' Custom manager for preliminary custodial histories
    '''
    def _get_non_empty_histories(self):
        return self.get_queryset().exclude(
            Q(preliminary_custodial_history__exact='') |
            Q(preliminary_custodial_history__isnull=True)
        )

    def flatten_atom(self, version: ExportVersion) -> dict:
        super().flatten_atom(version)
        self._get_non_empty_histories().aggregate(
            archivalHistory=DefaultConcat('preliminary_custodial_history')
        )

    def flatten_caais(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten custodial histories in queryset to export them in a CSV.
        '''
        super().flatten_caais(version)
        self._get_non_empty_histories().aggregate(
            preliminaryCustodialHistories=DefaultConcat('preliminary_custodial_history')
        )


class PreliminaryCustodialHistory(models.Model):
    ''' 2.2 Preliminary Custodial History (Repeatable - Optional)

    Information about the chain of agents, in addition to the creator(s), that
    have exercised custody or control over the material at all stages in its
    existence.
    '''

    class Meta:
        verbose_name_plural = gettext('Preliminary custodial histories')
        verbose_name = gettext('Preliminary custodial history')

    objects = PreliminaryCustodialHistoryManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preliminary_custodial_histories')
    preliminary_custodial_history = models.TextField(null=False, help_text=gettext(
        "Provide relevant custodial history information in accordance with the "
        "repository's descriptive standard. Record the successive transfers of "
        "ownership, responsibility and/or custody of the accessioned material "
        "prior to its transfer to the repository"
    ))

    def __str__(self):
        return f'Preliminary Custodial History #{self.id}'


class ExtentType(AbstractTerm):
    ''' 3.2.1 Extent Type (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Extent types')
        verbose_name = gettext('Extent type')
ExtentType._meta.get_field('name').help_text = gettext(
    "Record the extent statement type in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class ContentType(AbstractTerm):
    ''' 3.2.3 Content Type (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Content types')
        verbose_name = gettext('Content type')
ContentType._meta.get_field('name').help_text = gettext(
    "Record the type of material contained in the units measured, i.e., the "
    "genre of the material"
)


class CarrierType(AbstractTerm):
    ''' 3.2.4 Carrier Type (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Carrier types')
        verbose_name = gettext('Content type')
CarrierType._meta.get_field('name').help_text = gettext(
    "Record the physical format of an object that supports or carries archival "
    "materials using a controlled vocabulary maintained by the repository"
)


class ExtentStatementManager(models.Manager):
    ''' Custom manager for extent statements
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Convert the extent statements into a flat dictionary structure
        '''

        if self.get_queryset().count() == 0:
            return {}

        extent_types = []
        quantities = []
        content_types = []
        carrier_types = []
        extent_notes = []

        is_atom = ExportVersion.is_atom(version)

        def get_extent_attr(extent, attrs):
            value = get_nested_attr(extent, attrs)
            if value:
                return value
            return '' if is_atom else 'NULL'

        for extent in self.get_queryset().all():
            get_field = partial(get_extent_attr, extent)

            extent_types.append(get_field('extent_type,name'))
            quantities.append(get_field('quantity_and_unit_of_measure'))
            content_types.append(get_field('content_type,name'))
            carrier_types.append(get_field('carrier_type,name'))
            extent_notes.append(get_field('extent_note'))

        if not is_atom:
            return {
                'extentType': '|'.join(extent_types),
                'quantityAndUnitOfMeasures': '|'.join(quantities),
                'contentTypes': '|'.join(content_types),
                'carrierTypes': '|'.join(carrier_types),
                'extentNotes': '|'.join(extent_notes),
            }
        else:
            return {
                'receivedExtentUnits': '|'.join(quantities)
            }


class ExtentStatement(models.Model):
    ''' 3.2 Extent Statement (Repeatable - One Mandatory)

    The physical or logical quantity and type of material.
    '''

    class Meta:
        verbose_name = gettext('Extent statement')
        verbose_name_plural = gettext('Extent statements')

    objects = ExtentStatementManager()

    metadata = models.ForeignKey(
        Metadata, on_delete=models.CASCADE, null=False,
        related_name='extent_statements'
    )

    # 3.2.1 Extent Type
    # A term that characterizes the nature of each extent statement.
    extent_type = models.ForeignKey(
        ExtentType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements', help_text=gettext(
            "Record the extent statement type in accordance with a controlled "
            "vocabulary maintained by the repository."
        )
    )

    # 3.2.2 Quantity and Unit of Measure
    # The number and unit of measure expressing the quantity of the extent.
    quantity_and_unit_of_measure = models.CharField(
        max_length=256, null=False, blank=False, default=gettext('Not specified'),
        help_text=gettext((
        "Record the number and unit of measure expressing the quantity of the "
        "extent (e.g., 5 files, totalling 2.5MB)"
    )))

    # 3.2.3 Content Type
    # The type of material contained in the units measured, considered as a form
    # of communication or documentary genre.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements', help_text=gettext(
            "Record the type of material contained in the units measured, "
            "considered as a form of communication or documentary genre."
        )
    )

    # 3.2.4 Carrier Type
    # The physical format of an object that supports or carries archival
    # materials.
    carrier_type = models.ForeignKey(
        CarrierType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements'
    )

    # 3.2.5 Extent Note
    # Additional information related to the number and type of units received,
    # retained, or removed not otherwise recorded.
    extent_note = models.TextField(
        blank=True, default='', help_text=gettext(
            "Record additional information related to the number and type of "
            "units received, retained, or removed not otherwise recorded"
    ))

    def __str__(self):
        return f'Extent Statement #{self.id}'


class PreliminaryScopeAndContentManager(models.Manager):
    ''' Custom manager for preliminary scope and content
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten scope and contents for exporting in a CSV
        '''
        contents = self.get_queryset().values_list(
            'preliminary_scope_and_content', flat=True
        )

        if not contents:
            return {}

        if version == ExportVersion.CAAIS_1_0:
            return {
                'preliminaryScopeAndContent': '|'.join(contents)
            }
        else:
            return {
                'scopeAndContent': '. '.join([
                    c.rstrip('. ') for c in contents
                ])
            }


class PreliminaryScopeAndContent(models.Model):
    ''' 3.3 Preliminary Scope and Content
    '''

    class Meta:
        verbose_name_plural = gettext('Preliminary scope and contents')
        verbose_name = gettext('Preliminary scope and content')

    objects = PreliminaryScopeAndContentManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preliminary_scope_and_contents')

    preliminary_scope_and_content = models.TextField(null=False, help_text=gettext(
        "Record a preliminary description that may include: functions and "
        "activities that resulted in the material's generation, dates, the "
        "geographic area to which the material pertains, subject matter, "
        "arrangement, classification, and documentary forms"
    ))

    def __str__(self):
        return f'Preliminary Scope and Content #{self.id}'


class LanguageOfMaterialManager(models.Manager):
    ''' Custom manager for language of material
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten languages into a dict so that they can be exported in a CSV.
        '''

        languages = self.get_queryset().values_list(
            'language_of_material', flat=True,
        )

        if not languages:
            return {}

        if version == ExportVersion.CAAIS_1_0:
            return {
                'languageOfMaterial': '|'.join(languages)
            }
        else:
            language_list = ', '.join(languages)
            return {
                'scopeAndContent': f"Language of material: {language_list}"
            }

    def get_caais_metadata(self):
        languages = []
        for lang in self.get_queryset().all():
            languages.append(lang.language_of_material)
        return languages


class LanguageOfMaterial(models.Model):
    ''' 3.4 Language of Material (Repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Language of materials')
        verbose_name = gettext('Language of material')

    objects = LanguageOfMaterialManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='language_of_materials')

    language_of_material = models.CharField(max_length=128, null=False, help_text=gettext(
        "Record, at a minimum, the language that is predominantly found in the "
        "accessioned material"
    ))

    def __str__(self):
        return f'Language of Material #{self.id}'


class StorageLocationManager(models.Manager):
    ''' Custom manager for storage locations
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten storage locations into a dictionary
        '''
        if self.get_queryset().count() == 0:
            return {}

        locations = self.get_queryset().values_list(
            'storage_location', flat=True
        )

        if version == ExportVersion.CAAIS_1_0:
            return {'storageLocation': '|'.join(locations)}
        else:
            return {'locationInformation': '. '.join([
                l.rstrip('. ') for l in locations
            ])}

    def get_caais_metadata(self):
        locations = []
        for location in self.get_queryset().all():
            locations.append(location.storage_location)
        return locations


class StorageLocation(models.Model):
    ''' 4.1 Storage Location (Repeatable)
    '''

    class Meta:
        verbose_name_plural = 'Storage locations'
        verbose_name = 'Storage location'

    objects = StorageLocationManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='storage_locations')

    storage_location = models.TextField(null=False, help_text=gettext(
        "Record the physical and/or digital location(s) within the repository "
        "in which the accessioned material is stored"
    ))

    def __str__(self):
        return f'Storage Location #{self.id}'


class RightsType(AbstractTerm):
    ''' 4.2.1 Rights Type (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Rights types'
        verbose_name = 'Rights'
RightsType._meta.get_field('name').help_text = gettext(
    "Record the rights statement type in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class RightsManager(models.Manager):
    ''' Custom manager for rights
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Convert rights in queryset to a flat dictionary
        '''
        # There is no equivalent field in AtoM for rights
        if ExportVersion.is_atom(version) or self.get_queryset().count() == 0:
            return {}

        types = []
        values = []
        notes = []

        for rights in self.get_queryset().all():
            if rights.rights_type and rights.rights_type.name:
                types.append(str(rights.rights_type.name))
            else:
                types.append('NULL')
            if rights.rights_value:
                values.append(rights.rights_value)
            else:
                values.append('NULL')
            if rights.rights_note:
                notes.append(rights.rights_note)
            else:
                notes.append('NULL')

        return {
            'rightsType': '|'.join(types),
            'rightsValue': '|'.join(values),
            'rightsNote': '|'.join(notes),
        }


class Rights(models.Model):
    ''' 4.2 Rights (Repeatable)
    '''

    class Meta:
        verbose_name_plural = 'Rights'
        verbose_name = 'Rights'

    objects = RightsManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='rights')

    rights_type = models.ForeignKey(RightsType, on_delete=models.SET_NULL,
                                    null=True, related_name='rights_type')

    rights_value = models.TextField(blank=True, default='', help_text=gettext(
        "Record the nature and duration of the permission granted or "
        "restriction imposed. Specify where the condition applies only to part "
        "of the accession"
    ))

    rights_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information relevant to describing the rights "
        "statement"
    ))

    def __str__(self):
        return f'Rights Statement #{self.id}'


class MaterialAssessmentType(AbstractTerm):
    """ 4.3.1 Material Assessment Type (Repeatable)
    """
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Material Assessment Types'
        verbose_name = 'Material Assessment Type'

MaterialAssessmentType._meta.get_field('name').help_text = gettext(
    "Record the material assessment statement type in accordance with a controlled "
    "vocabulary maintained by the repository."
)


class MaterialAssessmentManager(models.Manager):
    """ Custom manager for preservation requirements
    """

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        """ Convert preservation in queryset to a flat dictionary
        """
        if self.get_queryset().count() == 0:
            return {}

        types = []
        values = []
        notes = []
        plans = []

        for assessments in self.get_queryset().all():
            if assessments.assessment_type and assessments.assessment_type.name:
                types.append(str(assessments.assessment_type.name))
            else:
                types.append('NULL')
            values.append(assessments.assessment_value or 'NULL')
            notes.append(assessments.assessment_note or 'NULL')
            plans.append(assessments.assessment_plan or 'NULL')

        if version == ExportVersion.CAAIS_1_0:
            return {
                'materialAssessmentStatementType': '|'.join(types),
                'materialAssessmentStatementValue': '|'.join(values),
                'materialAssessmentStatementNote': '|'.join(notes),
                'materialAssessmentActionPlan': '|'.join(plans),
            }
        else:
            return {
                'physicalCondition': '|'.join([f'Assessment Type: {x}; Statement: {y}' for
                                               x, y in zip(types, values)])
            }

    def get_caais_metadata(self):
        material_assessments = []
        for assessment in self.get_queryset().all():
            material_assessments.append({
                'material_assessment_statement_type': str(assessment.assessment_type.name),
                'material_assessment_statement_value': assessment.assessment_value,
                'material_assessment_action_plan': assessment.assessment_plan,
                'material_assessment_statement_note': assessment.assessment_note,
            })
        return material_assessments


class MaterialAssessmentStatement(models.Model):
    """ 4.3 Material Assessment Statement (Repeatable)
    """

    class Meta:
        verbose_name_plural = 'Material Assessment Statements'
        verbose_name = 'Material Assessment Statement'

    objects = MaterialAssessmentManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='material_assessments')

    assessment_type = models.ForeignKey(MaterialAssessmentType, on_delete=models.SET_NULL, null=True,
                                        related_name='material_assessment_types')

    assessment_value = models.TextField(blank=True, default='', help_text=gettext(
        "Record information about the assessment of the material with respect to its physical "
        "condition, dependencies, processing or access."
    ))

    assessment_plan = models.TextField(blank=True, default='', help_text=gettext(
        "Record the planned response to each of the physical requirements for preservation "
        "and access to the material."
    ))

    assessment_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information relevant to the long-term preservation of the material."
    ))

    def __str__(self):
        return f'Preservation Requirement #{self.id}'


class EventType(AbstractTerm):
    """ 5.1.1 Event Type """
    class Meta:
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'
EventType._meta.get_field('name').help_text = gettext(
    "Record the event type in accordance with a controlled vocabulary maintained by the repository"
)


class EventManager(models.Manager):

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        # There is no equivalent for event in AtoM
        if self.get_queryset().count() == 0 or ExportVersion.is_atom(version):
            return {}

        types = []
        dates = []
        agents = []
        notes = []

        for events in self.get_queryset().all():
            if events.event_type and events.event_type.name:
                types.append(str(events.event_type.name))
            else:
                types.append('NULL')
            dates.append(events.event_date.strftime(r'%Y-%m-%d %H:%M:%S %Z') or 'NULL')
            agents.append(events.event_agent or 'NULL')
            notes.append(events.event_note or 'NULL')

        return {
            'eventType': '|'.join(types),
            'eventDate': '|'.join(dates),
            'eventAgent': '|'.join(agents),
            'eventNote': '|'.join(notes),
        }

    def get_caais_metadata(self):
        events = []
        for event in self.get_queryset().all():
            events.append({
                'event_type': str(event.event_type.name),
                'event_date': event.event_date.strftime(r'%Y-%m-%d %H:%M:%S %Z'),
                'event_agent': event.event_agent,
                'event_note': event.event_note,
            })
        return events


class Event(models.Model):
    """ 5.1 Event (Repeatable) """
    class Meta:
        verbose_name_plural = 'Events'
        verbose_name = 'Event'

    objects = EventManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='events')
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, related_name='event_type')
    event_date = models.DateTimeField(auto_now_add=True)
    event_agent = models.CharField(max_length=256, null=False, help_text=gettext(
        "Record the name of the staff member or application responsible for the event."
    ))
    event_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information relevant to describing the event."
    ))

    def __str__(self):
        return f'Event: #{self.id}'


class GeneralNoteManager(models.Manager):

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        # There is no equivalent for generalNote in AtoM
        if self.get_queryset().count() == 0 or ExportVersion.is_atom(version):
            return {}

        notes = []
        for note in self.get_queryset().all():
            notes.append(note.note or 'NULL')
        return {
            'generalNote': '|'.join(notes)
        }

    def get_caais_metadata(self):
        notes = []
        for note in self.get_queryset().all():
            notes.append(note.note)
        return notes


class GeneralNote(models.Model):
    """ 6.1 General Note """
    class Meta:
        verbose_name = 'General Note'
        verbose_name_plural = 'General Notes'

    objects = GeneralNoteManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='general_notes')
    note = models.TextField(blank=True, default='', help_text=gettext(
        "To provide an open text element for repositories to record any relevant information not accommodated "
        "elsewhere in this standard."
    ))


class DateOfCreationOrRevisionType(AbstractTerm):
    class Meta:
        verbose_name = 'Date of Creation or Revision Type'
        verbose_name_plural = 'Date of Creation or Revision Types'
DateOfCreationOrRevisionType._meta.get_field('name').help_text = gettext(
    "Record the action type in accordance with a controlled vocabulary maintained by the repository."
)


class DateOfCreationOrRevisionManager(models.Manager):

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        if self.get_queryset().count() == 0:
            return {}

        types = []
        dates = []
        agents = []
        notes = []

        date_format = r'%Y-%m-%d %H:%M:%S %Z' if version == ExportVersion.CAAIS_1_0 else r'%Y-%m-%d'

        for revision in self.get_queryset().all():
            types.append(revision.action_type.name or 'NULL')
            dates.append(revision.action_date.strftime(date_format) or 'NULL')
            agents.append(revision.action_agent or 'NULL')
            notes.append(revision.action_note or 'NULL')

        if version == ExportVersion.CAAIS_1_0:
            return {
                'actionType': '|'.join(types),
                'actionDate': '|'.join(dates),
                'actionAgent': '|'.join(agents),
                'actionNote': '|'.join(notes)
            }
        elif version == ExportVersion.ATOM_2_1:
            return {
                'creators': '|'.join(agents)
            }
        elif version == ExportVersion.ATOM_2_2:
            return {
                'creators': '|'.join(agents),
                'creationDatesType': '|'.join(types),
                'creationDates': '|'.join(dates),
                'creationDatesStart': '|'.join(dates),
                'creationDatesEnd': '|'.join(dates),
            }
        else:
            return {
                'creators': '|'.join(agents),
                'eventTypes': '|'.join(types),
                'eventDates': '|'.join(dates),
                'eventStartDates': '|'.join(dates),
                'eventEndDates': '|'.join(dates),
            }

    def __str__(self):
        return f'DateOfCreationOrRevision #{self.id}'

    def get_caais_metadata(self):
        revisions = []
        for revision in self.get_queryset().all():
            revisions.append({
                'action_type': revision.action_type.name,
                'action_date': revision.action_date.strftime(r'%Y-%m-%d %H:%M:%S %Z'),
                'action_agent': revision.action_agent,
                'action_note': revision.action_note,
            })
        return revisions


class DateOfCreationOrRevision(models.Model):
    """ 7.3 Date of Creation or Revision """
    class Meta:
        verbose_name = 'Date of Creation or Revision'
        verbose_name_plural = 'Dates of Creation or Revision'

    objects = DateOfCreationOrRevisionManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='date_creation_revisions')
    action_type = models.ForeignKey(DateOfCreationOrRevisionType, on_delete=models.SET_NULL, null=True,
                                    related_name='action_type')
    action_date = models.DateTimeField(auto_now_add=True, help_text=gettext(
        "Record the date on which the action (creation or revision) occurred."
    ))
    action_agent = models.CharField(max_length=255, blank=False, default='', help_text=gettext(
        "Record the name of the staff member who performed the action (creation or revision) on the accession record."
    ))
    action_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any information summarizing actions applied to the accession record."
    ))
