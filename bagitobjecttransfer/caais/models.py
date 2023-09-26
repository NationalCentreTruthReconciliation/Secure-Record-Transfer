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
from collections import OrderedDict

from django.conf import settings
from django.db import models
from django.utils.translation import gettext
from django_countries.fields import CountryField

from caais.dates import EventDateParser, UnknownDateFormat
from caais.export import ExportVersion
from caais.managers import (
    MetadataManager,
    IdentifierManager,
    ArchivalUnitManager,
    DispositionAuthorityManager,
    SourceOfMaterialManager,
    PreliminaryCustodialHistoryManager,
    ExtentStatementManager,
    PreliminaryScopeAndContentManager,
    LanguageOfMaterialManager,
    StorageLocationManager,
    RightsManager,
    PreservationRequirementsManager,
    AppraisalManager,
    AssociatedDocumentationManager,
    EventManager,
    GeneralNoteManager,
    DateOfCreationOrRevisionManager,
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


class AcquisitionMethod(AbstractTerm):
    ''' **Acquisition Method** [CAAIS, Section 1.5]

    Definition: *The process by which a repository acquires material.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the acquisition method
        description (TextField): A description of the acquisition method
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Acquisition Methods')
        verbose_name = gettext('Acquisition Method')
AcquisitionMethod._meta.get_field('name').help_text = gettext(
    "Record the acquisition method in accordance with a controlled vocabulary"
)


class Status(AbstractTerm):
    ''' **Status** [CAAIS, Section 1.7]

    Definition: *The current position of the material with respect to the
    repository's workflows and business processes.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the status
        description (TextField): A description for the status term
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Statuses')
        verbose_name = gettext('Status')
Status._meta.get_field('name').help_text = gettext(
    "Record the current position of the material with respect to the "
    "repository's workflows and business processes using a controlled "
    "vocabulary"
)


class Metadata(models.Model):
    ''' Top-level container for all CAAIS metadata. Contains all simple
    non-repeatable fields. Any repeatable field is represented by a separate
    model with a ForeignKey.

    For **repeatable fields** associated with this model, see:

    * :py:class:`~caais.models.Identifier` [CAAIS, Section 1.2]

        * Access via related with :code:`self.identifiers`

    * :py:class:`~caais.models.ArchivalUnit` [CAAIS, Section 1.4]

        * Access via related with :code:`self.archival_units`

    * :py:class:`~caais.models.DispositionAuthority` [CAAIS, Section 1.6]

        * Access via related with :code:`self.disposition_authorities`

    * :py:class:`~caais.models.SourceOfMaterial` [CAAIS, Section 2.1]

        * Access via related with :code:`self.source_of_materials`

    * :py:class:`~caais.models.PreliminaryCustodialHistory` [CAAIS, Section 2.2]

        * Accessible via related with :code:`self.preliminary_custodial_histories`

    * :py:class:`~caais.models.ExtentStatement` [CAAIS, Section 3.2]

        * Accessible via related with :code:`self.extent_statements`

    * :py:class:`~caais.models.PreliminaryScopeAndContent` [CAAIS, Section 3.3]

        * Accessible via related with :code:`self.preliminary_scope_and_contents`

    * :py:class:`~caais.models.LanguageOfMaterials` [CAAIS, Section 3.4]

        * Accessible via related with :code:`self.language_of_materials`

    * :py:class:`~caais.models.StorageLocation` [CAAIS, Section 4.1]

        * Accessible via related with :code:`self.storage_locations`

    * :py:class:`~caais.models.Rights` [CAAIS, Section 4.2]

        * Accessible via related with :code:`self.rights`

    * :py:class:`~caais.models.PreservationRequirements` [CAAIS, Section 4.3]

        * Accessible via related with :code:`self.preservation_requirements`

    * :py:class:`~caais.models.Appraisal` [CAAIS, Section 4.4]

        * Accessible via related with :code:`self.appraisals`

    * :py:class:`~caais.models.AssociatedDocumentation` [CAAIS, Section 4.5]

        * Accessible via related with :code:`self.associated_documentation`

    * :py:class:`~caais.models.Events` [CAAIS, Section 5.1]

        * Accessible via related with :code:`self.events`

    * :py:class:`~caais.models.GeneralNote` [CAAIS, Section 6.1]

        * Accessible via related with :code:`self.general_notes`

    * :py:class:`~caais.models.DateOfCreationOrRevision` [CAAIS, Section 7.2]

        * Accessible via related with :code:`self.date_of_creation_or_revisions`

    Attributes:
        repository (CharField):
            **Repository** [CAAIS, Section 1.1]. Definition: *The name of the
            institution that accepts legal responsibility for the accessioned
            material.*
        accession_title (CharField):
            **Accession Title** [CAAIS, Section 1.3]. Definition: *The name
            assigned to the material.*
        acquisition_method (ForeignKey):
            See :py:class:`~caais.models.AcquisitionMethod` [CAAIS, Section 1.5]
        status (ForeignKey):
            See :py:class:`~caais.models.Status` [CAAIS, Section 1.7]
        date_of_materials (CharField):
            **Date of Materials** [CAAIS, Section 3.1]. Definition: *A date or
            date range indicating when the materials were known or thought to
            have been created.*
        rules_or_conventions (CharField):
            **Rules or Conventions** [CAAIS, Section 7.1]. Definition: *The
            rules, conventions or templates that were used in creating or
            maintaining the accession record.*
        language_of_accession_record (CharField):
            **Language of Accession Record** [CAAIS, Section 7.2]. Definition:
            *The language(s) and script(s) used to record information in the
            accession record.*
    '''
    class Meta:
        verbose_name_plural = gettext('CAAIS Metadata')
        verbose_name = gettext('CAAIS Metadata')

    objects = MetadataManager()

    repository = models.CharField(
        null=False, max_length=512, blank=True, default='', help_text=gettext(
            "Give the authorized form(s) of the name of the institution in "
            "accordance with the repository's naming standard"
        )
    )

    accession_title = models.CharField(
        null=False, max_length=512, blank=True, default='', help_text=gettext(
            "Supply an accession title in accordance with the repository's "
            "descriptive standard, typically consisting of the creator's name(s) "
            "and the type of material"
        )
    )

    acquisition_method = models.ForeignKey(
        AcquisitionMethod, on_delete=models.SET_NULL, null=True
    )

    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)

    date_of_materials = models.CharField(
        null=False, max_length=512, blank=True, default='', help_text=gettext(
            "Provide a preliminary estimate of the date range or explicitly "
            "indicate if not it has yet been determined"
        )
    )

    rules_or_conventions = models.CharField(
        null=False, max_length=256, blank=True, default='', help_text=gettext(
            "Record information about the standards, rules or conventions that "
            "were followed when creating or maintaining the accession record."
        )
    )

    language_of_accession_record = models.CharField(
        null=False, max_length=256, blank=True, default='en', help_text=gettext(
            "Record the language(s) and script(s) used to create the accession "
            "record."
        )
    )

    def _create_flat_atom_representation(self, row: dict, version: ExportVersion):
        row.update(self.identifiers.flatten(version))
        row.update(self.archival_units.flatten(version))
        row.update(self.disposition_authorities.flatten(version))
        row.update(self.source_of_materials.flatten(version))
        row.update(self.preliminary_custodial_histories.flatten(version))
        row.update(self.extent_statements.flatten(version))
        row.update(self.storage_locations.flatten(version))
        row.update(self.rights.flatten(version))
        row.update(self.preservation_requirements.flatten(version))
        row.update(self.appraisals.flatten(version))
        row.update(self.associated_documentation.flatten(version))
        row.update(self.events.flatten(version))
        row.update(self.general_notes.flatten(version))
        row.update(self.dates_of_creation_or_revision.flatten(version))

        row['title'] = self.accession_title or 'No title'
        row['acquisitionType'] = self.acquisition_method.name if self.acquisition_method else ''
        row['processingStatus'] = self.status.name if self.status else ''

        # Special case - both related objects return scope and content - combine them
        scope_1 = self.preliminary_scope_and_contents.flatten(version).get('scopeAndContent', '')
        scope_2 = self.language_of_materials.flatten(version).get('scopeAndContent', '')
        row['scopeAndContent'] = '\n\n'.join(s for s in [
            scope_1,
            scope_2,
        ] if s)

        accession_id = self.identifiers.accession_identifier()
        row['accessionNumber'] = accession_id.identifier_value if accession_id else ''

        row['culture'] = 'en'

        if self.date_of_materials and not version == ExportVersion.ATOM_2_1:
            try:
                parser = EventDateParser(
                    unknown_date=settings.CAAIS_UNKNOWN_DATE_TEXT,
                    unknown_start_date=settings.CAAIS_UNKNOWN_START_DATE,
                    unknown_end_date=settings.CAAIS_UNKNOWN_END_DATE,
                    timid=False
                )
                parsed_date, date_range = parser.parse_date(self.date_of_materials)
                if len(date_range) == 1:
                    start_date, end_date = date_range[0], date_range[0]
                else:
                    start_date, end_date = date_range[0], date_range[1]

                if version == ExportVersion.ATOM_2_2:
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
                if version == ExportVersion.ATOM_2_2:
                    row['creationDatesType'] = 'Creation'
                    row['creationDates'] = settings.CAAIS_UNKNOWN_DATE_TEXT
                    row['creationDatesStart'] = settings.CAAIS_UNKNOWN_START_DATE
                    row['creationDatesEnd'] = settings.CAAIS_UNKNOWN_END_DATE
                else:
                    row['eventTypes'] = 'Creation'
                    row['eventDates'] = settings.CAAIS_UNKNOWN_DATE_TEXT
                    row['eventStartDates'] = settings.CAAIS_UNKNOWN_START_DATE
                    row['eventEndDates'] = settings.CAAIS_UNKNOWN_END_DATE


    def _create_flat_caais_representation(self, row: dict, version: ExportVersion):
        # Section 1
        row['repository'] = self.repository or ''
        row.update(self.identifiers.flatten(version))
        row['accessionTitle'] = self.accession_title or 'No title'
        row.update(self.archival_units.flatten(version))
        row['acquisitionMethod'] = self.acquisition_method.name if self.acquisition_method else ''
        row.update(self.disposition_authorities.flatten(version))
        row['status'] = self.status.name if self.status else ''

        # Section 2
        row.update(self.source_of_materials.flatten(version))
        row.update(self.preliminary_custodial_histories.flatten(version))

        # Section 3
        row['dateOfMaterials'] = self.date_of_materials or ''
        row.update(self.extent_statements.flatten(version))
        row.update(self.preliminary_scope_and_contents.flatten(version))
        row.update(self.language_of_materials.flatten(version))

        # Section 4
        row.update(self.storage_locations.flatten(version))
        row.update(self.rights.flatten(version))
        row.update(self.preservation_requirements.flatten(version))
        row.update(self.appraisals.flatten(version))
        row.update(self.associated_documentation.flatten(version))

        # Section 5
        row.update(self.events.flatten(version))

        # Section 6
        row.update(self.general_notes.flatten(version))

        # Section 7
        row['rulesOrConventions'] = self.rules_or_conventions or ''
        row.update(self.dates_of_creation_or_revision.flatten(version))
        row['languageOfAccessionRecord'] = self.language_of_accession_record or ''


    def create_flat_representation(self, version=ExportVersion.CAAIS_1_0) -> dict:
        ''' Convert this model and all related models into a flat dictionary
        suitable to be written to a CSV or used as the metadata fields for a
        BagIt bag.

        Note that some CAAIS fields do not map well to AtoM fields, so some
        information is dropped when using an AtoM export version. For maximum
        compatibility, convert using the CAAIS export version when possible.

        Args:
            version (ExportVersion):
                The flat representation type to export. Can be a CAAIS version
                or an AtoM version.

        Returns:
            (dict):
                A dictionary containing all fields in this model as well as all
                related models (where possible).
        '''
        row = OrderedDict()
        for col in version.fieldnames:
            row[col] = ''
        if ExportVersion.is_atom(version):
            self._create_flat_atom_representation(row, version)
        else:
            self._create_flat_caais_representation(row, version)
        return row


    def update_accession_id(self, accession_id: str, commit: bool = True):
        ''' Update the accession identifier value, if an accession identifier
        exists.

        Args:
            accession_id (str): The new accession identifier
            commit (bool): Saves this model if a change is made if True
        '''
        a_id = self.identifiers.accession_identifier()
        if a_id is not None:
            a_id.identifier_value = accession_id
            if commit:
                a_id.save()


    def __str__(self):
        return self.accession_title or 'No title'


class Identifier(models.Model):
    ''' **Identifiers** [CAAIS, Section 1.2]

    Definition: *Alphabetic, numeric, or alpha-numeric codes assigned to
    accessioned material, parts of the material, or accruals for purposes of
    unique for purposes of identification.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.identifiers`
        identifier_type (CharField):
            **Identifier Type** [CAAIS, Section 1.2.1]. Definition: *A term or
            phrase that characterizes the nature of the identifier*
        identifier_value (CharField):
            **Identifier Value** [CAAIS, Section 1.2.2]. Definition: *A code
            that is assigned to the material to support identification in the
            course of processes and activities such as acquisition, transfer,
            ingest, and conservation.*
        identifier_note (CharField):
            **Identifier Note** [CAAIS, Section 1.2.3]. Definition: *Additional
            information about the identifier, including contextual information
            on the purpose of the identifier.*
    '''
    class Meta:
        verbose_name_plural = gettext('Identifiers')
        verbose_name = gettext('Identifier')

    objects = IdentifierManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='identifiers')

    identifier_type = models.CharField(
        max_length=128, null=False, blank=True, default='', help_text=gettext(
        "Record the identifier type in accordance with a controlled vocabulary "
        "maintained by the repository"
    ))

    identifier_value = models.CharField(
        max_length=128, null=False, blank=False, help_text=gettext(
        "Record the other identifier value as received or generated by the "
        "repository"
    ))

    identifier_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
        "Record any additional information that clarifies the purpose, use or "
        "generation of the identifier."
    ))

    def __str__(self):
        if self.identifier_type:
            return f'{self.identifier_value} ({self.identifier_type})'
        return self.identifier_value


class ArchivalUnit(models.Model):
    '''**Archival Unit** [CAAIS, Section 1.4]

    Definition: *The archival unit or the aggregate to which the accessioned
    material belongs.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.archival_units`
        archival_unit (TextField):
            The text content of CAAIS, Section 1.4.
    '''
    class Meta:
        verbose_name_plural = gettext('Archival Units')
        verbose_name = gettext('Archival Unit')

    objects = ArchivalUnitManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='archival_units')

    archival_unit = models.TextField(null=False, blank=False, help_text=gettext(
        "Record the reference code and/or title of the archival unit to which "
        "the accession belongs"
    ))

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class DispositionAuthority(models.Model):
    ''' **Disposition Authority** [CAAIS, Section 1.6]

    Definition: *A reference to policies, directives, and agreements that
    prescribe and allow for the transfer of material to a repository.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.disposition_authorities`
        disposition_authority (TextField):
            The text content of CAAIS, Section 1.6.
    '''
    class Meta:
        verbose_name_plural = gettext('Disposition Authorities')
        verbose_name = gettext('Disposition Authority')

    objects = DispositionAuthorityManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='disposition_authorities')

    disposition_authority = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Record information about any legal instruments that apply to the "
            "accessioned material. Legal instruments include statutes, records "
            "schedules or disposition authorities, and donor agreements"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class SourceType(AbstractTerm):
    ''' **Source Type** [CAAIS, Section 2.1.1]

    Definition: *A term describing the nature of the source.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the source type
        description (TextField): A description of the source type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source Types')
        verbose_name = gettext('Source Type')
SourceType._meta.get_field('name').help_text = gettext(
    "Record the source in accordance with a controlled vocabulary maintained "
    "by the repository"
)


class SourceRole(AbstractTerm):
    ''' **Source Role** [CAAIS, Section 2.1.4]

    Definition: *The relationship of the named source to the material.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the source role
        description (TextField): A description of the source role
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source Roles')
        verbose_name = gettext('Source Role')
SourceRole._meta.get_field('name').help_text = gettext(
    "Record the source role (when known) in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class SourceConfidentiality(AbstractTerm):
    ''' **Source Confidentiality** [CAAIS, Section 2.1.6]

    Definition: *An instruction to maintain information about the source in
    confidence.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the source confidentiality
        description (TextField): A description of the source confidentiality
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source Confidentialities')
        verbose_name = gettext('Source Confidentiality')
SourceConfidentiality._meta.get_field('name').help_text = gettext(
    "Record source statements or source information that is for internal use "
    "only by the repository. Repositories should develop a controlled "
    "vocabulary with terms that can be translated into clear rules for "
    "handling source information"
)


class SourceOfMaterial(models.Model):
    ''' **Source of Material** [CAAIS, Section 2.1]

    Definition: *A corporate body, person or family responsible for the
    creation, use or transfer of the accessioned material.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.source_of_materials`
        source_type (ForeignKey):
            See :py:class:`~caais.models.SourceType` [CAAIS, Section 2.1.1]
        source_name (CharField):
            **Source Name** [CAAIS, Section 2.1.2]. Definition: *The proper name
            of the source of the material.*
        contact_name (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The name of the contact person
        job_title (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The job title of the contact person
        organization (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The organization the source is a member of, or the organization the
            source *is*
        phone_number (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The phone number the source can be contacted with
        email_address (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The email address the source can be contacted with
        address_line_1 (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The first line of the address where the source resides or operates in
        address_line_2 (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The second line of the address where the source resides or operates
            in
        city (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The city the source resides or operates in
        region (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The region the source resides or operates in, i.e., the province or
            state
        postal_or_zip_code (CharField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The source's postal or zip code
        country (CountryField):
            An extension of **Source Contact Information** [CAAIS, Section 2.1.3]
            The country the source resides or operates in
        source_role (ForeignKey):
            See :py:class:`~caais.models.SourceRole` [CAAIS, Section 2.1.4]
        source_note (TextField):
            **Source Note** [CAAIS, Section 2.1.5]. Definition: *An open element
            to capture any additional information about the source, or
            circumstances surrounding their role.*
        source_confidentiality (ForeignKey):
            See :py:class:`~caais.models.SourceConfidentiality` [CAAIS, Section
            2.1.6]
    '''
    class Meta:
        verbose_name_plural = gettext('Sources of Material')
        verbose_name = gettext('Source of Material')

    objects = SourceOfMaterialManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='source_of_materials')

    source_type = models.ForeignKey(SourceType, on_delete=models.SET_NULL,
                                    null=True, related_name='source_of_materials')

    source_name = models.CharField(
        max_length=256, null=False, blank=True, default='', help_text=gettext(
        "Record the source name in accordance with the repository's "
        "descriptive standard"
    ))

    contact_name = models.CharField(max_length=256, blank=True, default='')
    job_title = models.CharField(max_length=256, blank=True, default='')
    organization = models.CharField(max_length=256, blank=True, default='')
    phone_number = models.CharField(max_length=32, blank=True, default='')
    email_address = models.CharField(max_length=256, blank=True, default='')
    address_line_1 = models.CharField(max_length=256, blank=True, default='')
    address_line_2 = models.CharField(max_length=256, blank=True, default='')
    city = models.CharField(max_length=128, blank=True, default='')
    region = models.CharField(max_length=128, blank=True, default='')
    postal_or_zip_code = models.CharField(max_length=16, blank=True, default='')
    country = CountryField(null=True)

    source_role = models.ForeignKey(
        SourceRole, on_delete=models.SET_NULL, null=True,
        related_name='source_of_materials'
    )

    source_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information about the source of the accessioned "
        "materials. If the source performed the role for only a specific "
        "period of time (e.g. was a custodian for several years), record the "
        "dates in this element"
    ))

    source_confidentiality = models.ForeignKey(
        SourceConfidentiality, on_delete=models.SET_NULL, null=True,
        related_name='source_of_materials'
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class PreliminaryCustodialHistory(models.Model):
    ''' **Preliminary Custodial History** [CAAIS, Section 2.2]

    Definition: *Information about the chain of agents, in addition to the
    creator(s), that have exercised custody or control over the material at all
    stages in its existence.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.preliminary_custodial_histories`
        preliminary_custodial_history (TextField):
            The text content of CAAIS, Section 2.2.
    '''
    class Meta:
        verbose_name_plural = gettext('Preliminary Custodial Histories')
        verbose_name = gettext('Preliminary Custodial History')

    objects = PreliminaryCustodialHistoryManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preliminary_custodial_histories')

    preliminary_custodial_history = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Provide relevant custodial history information in accordance with "
            "the repository's descriptive standard. Record the successive "
            "transfers of ownership, responsibility and/or custody of the "
            "accessioned material prior to its transfer to the repository"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class ExtentType(AbstractTerm):
    ''' **Extent Type** [CAAIS, Section 3.2.1]

    Definition: *A term that characterizes the nature of each extent statement.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the extent type
        description (TextField): A description of the extent type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Extent types')
        verbose_name = gettext('Extent type')
ExtentType._meta.get_field('name').help_text = gettext(
    "Record the extent statement type in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class ContentType(AbstractTerm):
    ''' **Content Type** [CAAIS, Section 3.2.3]

    Definition: *The type of material contained in the units measured,
    considered as a form of communication or documentary genre.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the content type
        description (TextField): A description of the content type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Content types')
        verbose_name = gettext('Content type')
ContentType._meta.get_field('name').help_text = gettext(
    "Record the type of material contained in the units measured, i.e., the "
    "genre of the material"
)


class CarrierType(AbstractTerm):
    ''' **Carrier Type** [CAAIS, Section 3.2.4]

    Definition: *The physical format of an object that supports or carries
    archival materials.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the carrier type
        description (TextField): A description of the carrier type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Carrier types')
        verbose_name = gettext('Carrier type')
CarrierType._meta.get_field('name').help_text = gettext(
    "Record the physical format of an object that supports or carries archival "
    "materials using a controlled vocabulary maintained by the repository"
)


class ExtentStatement(models.Model):
    ''' **Extent Statement** [CAAIS, Section 3.2]

    Definition: *The physical or logical quantity and type of material.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.preliminary_custodial_histories`
        extent_type (ForeignKey):
            See :py:class:`~caais.models.ExtentType` [CAAIS, Section 3.2.1]
        quantity_and_unit_of_measure (TextField):
            **Quantity and Unit of Measure** [CAAIS, Section 3.2.2]. Definition:
            *The number and unit of measure expressing the quantity of the
            extent.*
        content_type (ForeignKey):
            See :py:class:`~caais.models.ContentType` [CAAIS, Section 3.2.3]
        carrier_type (ForeignKey):
            See :py:class:`~caais.models.CarrierType` [CAAIS, Section 3.2.4]
        extent_note (TextField):
            **Extent Note** [CAAIS, Section 3.2.5]. Definition: *Additional
            information related to the number and type of units received,
            retained, or removed not otherwise recorded.*
    '''
    class Meta:
        verbose_name = gettext('Extent Statement')
        verbose_name_plural = gettext('Extent Statements')

    objects = ExtentStatementManager()

    metadata = models.ForeignKey(
        Metadata, on_delete=models.CASCADE, null=False,
        related_name='extent_statements'
    )

    extent_type = models.ForeignKey(
        ExtentType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements', help_text=gettext(
            "Record the extent statement type in accordance with a controlled "
            "vocabulary maintained by the repository."
        )
    )

    quantity_and_unit_of_measure = models.TextField(
        null=False, blank=True, default='',
        help_text=gettext((
        "Record the number and unit of measure expressing the quantity of the "
        "extent (e.g., 5 files, totalling 2.5MB)"
    )))

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements', help_text=gettext(
            "Record the type of material contained in the units measured, "
            "considered as a form of communication or documentary genre."
        )
    )

    carrier_type = models.ForeignKey(
        CarrierType, on_delete=models.SET_NULL, null=True,
        related_name='extent_statements'
    )

    extent_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record additional information related to the number and type of "
            "units received, retained, or removed not otherwise recorded"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class PreliminaryScopeAndContent(models.Model):
    ''' **Preliminary Scope and Content** [CAAIS, Section 3.3]

    Definition: *A preliminary description of the functions and activities that
    generated the accessioned material as well as information about its
    arrangement (organizational structure or relationships) and documentary
    forms.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.preliminary_scope_and_contents`
        preliminary_scope_and_content (TextField):
            The text content of CAAIS, Section 3.3.
    '''
    class Meta:
        verbose_name_plural = gettext('Preliminary Scope and Content')
        verbose_name = gettext('Preliminary Scope and Content')

    objects = PreliminaryScopeAndContentManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preliminary_scope_and_contents')

    preliminary_scope_and_content = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Record a preliminary description that may include: functions and "
            "activities that resulted in the material's generation, dates, the "
            "geographic area to which the material pertains, subject matter, "
            "arrangement, classification, and documentary forms"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class LanguageOfMaterial(models.Model):
    ''' **Language of Material** [CAAIS, Section 3.4]

    Definition: *The language(s) and script(s) represented in the accessioned
    materials.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.language_of_materials`
        language_of_material (TextField):
            The text content of CAAIS, Section 3.4.
    '''
    class Meta:
        verbose_name_plural = gettext('Language of materials')
        verbose_name = gettext('Language of material')

    objects = LanguageOfMaterialManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='language_of_materials')

    language_of_material = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Record, at a minimum, the language that is predominantly found in "
            "the accessioned material"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class StorageLocation(models.Model):
    ''' **Storage Location** [CAAIS, Section 4.1]

    Definition: *The physical or logical location where the material resides.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.storage_locations`
        storage_location (TextField):
            The text content of CAAIS, Section 4.1.
    '''
    class Meta:
        verbose_name_plural = 'Storage Locations'
        verbose_name = 'Storage Location'

    objects = StorageLocationManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='storage_locations')

    storage_location = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Record the physical and/or digital location(s) within the "
            "repository in which the accessioned material is stored"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class RightsType(AbstractTerm):
    ''' **Rights Type** [CAAIS, Section 4.2.1]

    Definition: *A term that characterizes the nature of a rights statement.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the rights type
        description (TextField): A description of the rights type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Rights types'
        verbose_name = 'Rights'
RightsType._meta.get_field('name').help_text = gettext(
    "Record the rights statement type in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class Rights(models.Model):
    ''' **Rights** [CAAIS, Section 4.2]

    Definition: *The assertion of one or more rights pertaining to the
    material.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.rights`
        rights_type (ForeignKey):
            See :py:class:`~caais.models.RightsType` [CAAIS, Section 4.2.1]
        rights_value (TextField):
            **Rights Value** [CAAIS, Section 4.2.2]. Definition: *The parameters
            and conditions pertaining to the rights statement.*
        rights_note (TextField):
            **Rights Note** [CAAIS, Section 4.2.3]. Definition: *Additional
            information related to the rights statement not otherwise recorded.*
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
        return f'{self.__class__.__name__} #{self.id}'


class PreservationRequirementsType(AbstractTerm):
    ''' **Preservation Requirements Type** [CAAIS, Section 4.3.1]

    Definition: *A description of the material's physical state, dependency or
    preservation concerns identified.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the preservation requirements type
        description (TextField): A description of the preservation requirements type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Preservation Requirements Types'
        verbose_name = 'Preservation Requirements Type'
PreservationRequirementsType._meta.get_field('name').help_text = gettext(
    "Record information about the assessment of the material with respect to "
    "its physical condition, dependencies, processing or access."
)


class PreservationRequirements(models.Model):
    ''' **Preservation Requirements** [CAAIS, Section 4.3]

    Definition: *Information about physical condition and / or logical
    dependencies that need to be addressed by the repository to ensure the
    long-term preservation of the materials.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.preservation_requirements`
        preservation_requirements_type (ForeignKey):
            See :py:class:`~caais.models.PreservationRequirementsType` [CAAIS,
            Section 4.3.1]
        preservation_requirements_value (TextField):
            **Preservation Requirements Value** [CAAIS, Section 4.3.2].
            Definition: *A description of the material's physical state,
            dependency or preservation concerns identified.*
        preservation_requirements_note (TextField):
            **Preservation Requirements Note** [CAAIS, Section 4.3.3].
            Definition: *Additional information related to the preservation
            requirement not otherwise recorded.*
    '''
    class Meta:
        verbose_name_plural = 'Preservation Requirements'
        verbose_name = 'Preservation Requirements'

    objects = PreservationRequirementsManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preservation_requirements')

    preservation_requirements_type = models.ForeignKey(
        PreservationRequirementsType, on_delete=models.SET_NULL, null=True,
        related_name='preservation_requirements'
    )

    preservation_requirements_value = models.TextField(
        blank=True, default='', help_text=gettext(
            "Record information about the assessment of the material with "
            "respect to its physical condition, dependencies, processing or "
            "access"
        )
    )

    preservation_requirements_note = models.TextField(
        blank=True, default='', help_text=gettext(
            "Record any other information relevant to the long-term "
            "preservation of the material"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class AppraisalType(AbstractTerm):
    ''' **Appraisal Type** [CAAIS, Section 4.4.1]

    Definition: *A term that characterizes the nature of the appraisal.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the appraisal type
        description (TextField): A description of the appraisal type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Appraisal Types'
        verbose_name = 'Appraisal Type'
AppraisalType._meta.get_field('name').help_text = gettext(
    "Record the appraisal type in accordance with a controlled vocabulary "
    "maintained by the repository"
)


class Appraisal(models.Model):
    ''' **Appraisal** [CAAIS, Section 4.4]

    Definition: *Information about the assessment of value of the materials
    accessioned.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.appraisals`
        appraisal_type (ForeignKey):
            See :py:class:`~caais.models.AppraisalType` [CAAIS, Section 4.4.1]
        appraisal_value (TextField):
            **Appraisal Value** [CAAIS, Section 4.4.2]. Definition: *A statement
            identifying any decisions made on the appraisal and selection of
            material, or outlining monetary appraisal details.*
        appraisal_note (TextField):
            **Appraisal Note** [CAAIS, Section 4.4.3]. Definition: *Additional
            information related to the appraisal not otherwise recorded.*
    '''
    class Meta:
        verbose_name_plural = 'Appraisals'
        verbose_name = 'Appraisal'

    objects = AppraisalManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='appraisals')

    appraisal_type = models.ForeignKey(
        AppraisalType, on_delete=models.SET_NULL, null=True,
        related_name='appraisals'
    )

    appraisal_value = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Where the accession process includes appraisal activities, record "
            "the appraisal statement value."
        )
    )

    appraisal_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record any other information relevant to describing the appraisal "
            "activities."
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class AssociatedDocumentationType(AbstractTerm):
    ''' **Associated Documentation Type** [CAAIS, Section 4.5.1]

    Definition: *A term that characterizes the nature of the appraisal.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the associated documentation type
        description (TextField): A description of the associated documentation type
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Appraisal Types'
        verbose_name = 'Appraisal Type'
AssociatedDocumentationType._meta.get_field('name').help_text = gettext(
    "Where the accession process generates associated documents, record the "
    "associated documentation type in accordance with a controlled vocabulary "
    "maintained by the repository."
)


class AssociatedDocumentation(models.Model):
    ''' **Associated Documentation** [CAAIS, Section 4.5]

    Definition: *A reference to any documentation related to the material in the
    accession.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.appraisals`
        associated_documentation_type (ForeignKey):
            See :py:class:`~caais.models.AssociatedDocumentationType` [CAAIS,
            Section 4.5.1]
        associated_documentation_title (TextField):
            **Associated Documentation Title** [CAAIS, Section 4.5.2].
            Definition: *Name of the documentation related to the accessioned
            material*
        associated_documentation_note (TextField):
            **Associated Documentation Note** [CAAIS, Section 4.5.3].
            Definition: *Additional information related to associated
            documentation not otherwise recorded*
    '''
    class Meta:
        verbose_name_plural = 'Associated Documentation'
        verbose_name = 'Associated Documentation'

    objects = AssociatedDocumentationManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='associated_documentation')

    associated_documentation_type = models.ForeignKey(
        AssociatedDocumentationType, on_delete=models.SET_NULL, null=True,
        related_name='associated_documentation'
    )

    associated_documentation_title = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record the title of the associated documentation"
        )
    )

    associated_documentation_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record any other information relevant to describing documentation "
            "associated to the accessioned material"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class EventType(AbstractTerm):
    ''' **Event Type** [CAAIS, Section 5.1.1]

    Definition: *A term that characterizes the type of event documented in the
    accession process.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the event type
        description (TextField): A description of the event type
    '''
    class Meta:
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'
EventType._meta.get_field('name').help_text = gettext(
    "Record the event type in accordance with a controlled vocabulary "
    "maintained by the repository"
)


class Event(models.Model):
    ''' **Event** [CAAIS, Section 5.1]

    Definition: *The actions taken by repository staff throughout the accession
    process.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.events`
        event_type (ForeignKey):
            See :py:class:`~caais.models.EventType` [CAAIS, Section 5.1.1]
        event_date (DateTimeField):
            **Event Date** [CAAIS, Section 5.1.2]. Definition: *The calendar
            date on which the event occurred.* Time is automatically set to the
            current time when a new :code:`Event` is created.
        event_agent (TextField):
            **Event Agent** [CAAIS, Section 5.1.3]. Definition: *The repository
            staff member responsible for the event.*
        event_note (TextField):
            **Event Note** [CAAIS, Section 5.1.4]. Definition: *Additional
            information related to the event not otherwise recorded.*
    '''
    class Meta:
        verbose_name_plural = 'Events'
        verbose_name = 'Event'

    objects = EventManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='events')

    event_type = models.ForeignKey(
        EventType, on_delete=models.SET_NULL, null=True,
        related_name='event_type'
    )

    event_date = models.DateTimeField(auto_now_add=True)

    event_agent = models.CharField(
        max_length=256, null=False, blank=True, default='', help_text=gettext(
            "Record the name of the staff member or application responsible "
            "for the event"
        )
    )

    event_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record any other information relevant to describing the event."
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id} @ {str(self.event_date)}'



class GeneralNote(models.Model):
    ''' **General Note** [CAAIS, Section 6.1]

    Definition: *Additional information relating to the accession process or
    material that is not otherwise captured.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.general_notes`
        general_note (TextField):
            The text content of CAAIS, Section 6.1.
    '''
    class Meta:
        verbose_name = 'General Note'
        verbose_name_plural = 'General Notes'

    objects = GeneralNoteManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='general_notes')

    general_note = models.TextField(
        null=False, blank=False, help_text=gettext(
            "Record any other information relevant to the accession record or "
            "accessioning process"
        )
    )

    def __str__(self):
        return f'{self.__class__.__name__} #{self.id}'


class CreationOrRevisionType(AbstractTerm):
    ''' **Creation or Revision Type** [CAAIS, Section 7.2.1]

    Definition: *A term characterizing the nature of the action applied to the
    accession record.*

    Inherits :py:class:`~caais.models.AbstractTerm`

    Attributes:
        name (CharField): The name of the creation or revision type
        description (TextField): A description of the creation or revision type
    '''
    class Meta:
        verbose_name = 'Date of Creation or Revision Type'
        verbose_name_plural = 'Date of Creation or Revision Types'
CreationOrRevisionType._meta.get_field('name').help_text = gettext(
    "Record the action type in accordance with a controlled vocabulary "
    "maintained by the repository."
)


class DateOfCreationOrRevision(models.Model):
    ''' **Date of Creation or Revision** [CAAIS, Section 7.2]

    Definition: *Date(s) on which the accession record was created or revised.*

    Attributes:
        metadata (ForeignKey):
            Link to :py:class:`~caais.models.Metadata` object. Access instances
            of this model with :code:`metadata.dates_of_creation_or_revision`
        creation_or_revision_type (ForeignKey):
            See :py:class:`~caais.models.CreationOrRevisionType` [CAAIS, Section
            7.2.1]
        creation_or_revision_date (DateTimeField):
            **Creation or Revision Date** [CAAIS, Section 7.2.2]. Definition:
            *The date on which the action was applied to the accession record.*
            Time is automatically set to the current time when a new
            :code:`DateOfCreationOrRevision` is created.
        creation_or_revision_agent (CharField):
            **Creation or Revision Agent** [CAAIS, Section 7.2.3]. Definition:
            *The repository staff member responsible for the action applied to
            the accession record.*
        creation_or_revision_note (TextField):
            **Creation or Revision Note** [CAAIS, Section 7.2.4]. Definition:
            *Additional information describing the action performed on the
            accession record.*
    '''
    class Meta:
        verbose_name = 'Date of Creation or Revision'
        verbose_name_plural = 'Dates of Creation or Revision'

    objects = DateOfCreationOrRevisionManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='dates_of_creation_or_revision')

    creation_or_revision_type = models.ForeignKey(
        CreationOrRevisionType, on_delete=models.SET_NULL, null=True,
        related_name='dates_of_creation_or_revision'
    )

    creation_or_revision_date = models.DateTimeField(
        auto_now_add=True, help_text=gettext(
            "Record the date on which the action (creation or revision) "
            "occurred."
        )
    )

    creation_or_revision_agent = models.CharField(
        max_length=256, null=False, blank=True, default='', help_text=gettext(
            "Record the name of the staff member who performed the action "
            "(creation or revision) on the accession record"
        )
    )

    creation_or_revision_note = models.TextField(
        null=False, blank=True, default='', help_text=gettext(
            "Record any information summarizing actions applied to the "
            "accession record."
        )
    )
