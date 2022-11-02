''' Models describing the Canadian Archival Accession Information Standard v1.0:

http://archivescanada.ca/uploads/files/Documents/CAAIS_2019May15_EN.pdf
'''
from functools import partial
from typing import Union, Iterable

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext

from django_countries.fields import CountryField

from caais.dates import EventDateParser, UnknownDateFormat
from caais.export import ExportVersion


def get_nested_attr(model, attrs: Union[str, Iterable]):
    ''' Get one or more nested attributes as a string value from a model. If
    value does not exist or is Falsy, returns None.

    Args:
        model: Some model or object with attributes
        attrs (Union[str, Iterable]): A list of strings or a comma-delimited
            string of properties
    '''
    obj = model
    if isinstance(attrs, str):
        attr_list = map(str.strip, attrs.split(','))
    else:
        attr_list = attrs
    for attr in attr_list:
        try:
            obj = getattr(obj, attr)
        except AttributeError:
            return None
    if obj:
        return str(obj) or None
    return None


class AbstractTerm(models.Model):
    ''' An abstract class that can be used to define any term that consists of
    a name and a description.
    '''

    class Meta:
        abstract = True

    name = models.CharField(max_length=128, null=False, blank=False)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


class Status(AbstractTerm):
    ''' 1.7 Status (Non-repeatable)
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Accession statuses')
        verbose_name = gettext('Accession status')
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

    repository = models.CharField(max_length=128, null=True, help_text=gettext(
        "Give the authorized form(s) of the name of the institution in "
        "accordance with the repository's naming standard"
    ))
    accession_title = models.CharField(max_length=128, null=True, help_text=gettext(
        "Supply an accession title in accordance with the repository's "
        "descriptive standard, typically consisting of the creator's name(s) "
        "and the type of material"
    ))
    acquisition_method = models.CharField(max_length=128, null=True, help_text=gettext(
        "Record the acquisition method in accordance with a controlled "
        "vocabulary"
    ))
    # 1.7 Disposition Authority
    disposition_authority = models.TextField(null=True, help_text=gettext(
        "Record information about any legal instruments that apply to the "
        "accessioned material. Legal instruments include statutes, records "
        "schedules or disposition authorities, and donor agreements"
    ))
    # 2.2 Custodial History
    custodial_history = models.TextField(null=True, help_text=gettext(
        "Provide relevant custodial history information in accordance with the "
        "repository's descriptive standard. Record the successive transfers of "
        "ownership, responsibility and/or custody of the accessioned material "
        "prior to its transfer to the repository"
    ))

    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True,
                               related_name='metadatas')
    # 3.1 Date of Material
    date_of_material = models.CharField(max_length=128, null=True, help_text=gettext(
        "Provide a preliminary estimate of the date range or explicitly "
        "indicate if not it has yet been determined"
    ))
    # 3.3 Scope and Content
    scope_and_content = models.TextField(null=True, help_text=gettext(
        "Record a summary that includes: functions and activities that resulted in the material’s generation, dates, "
        "the geographic area to which the material pertains, subject matter, arrangement, classification, and "
        "documentary forms. This is recorded as a free text statement."
    ))

    # 7.1 Rules or Conventions
    rules_or_conventions = models.CharField(max_length=255, blank=True, default='', help_text=gettext(
        "Record information about the standards, rules or conventions that were followed when creating or maintaining "
        "the accession record. Indicate the software application if the accession record is based on a data entry "
        "template in a database or other automated system. Give the version number of the standard or software "
        "application where applicable."
    ))
    # 7.2 Level of detail
    level_of_detail = models.CharField(max_length=255, blank=True, default='', help_text=gettext(
        "Record the level of detail in accordance with a controlled vocabulary maintained by the repository."
    ))
    # 7.4 Language of record
    language_of_record = models.CharField(max_length=20, blank=True, default='en', help_text=gettext(
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
            row['status'] = self.status.name if self.status else ''
            row['dateOfMaterial'] = self.date_of_material or ''
            row['dispositionAuthority'] = self.disposition_authority or ''
            row['scopeAndContent'] = self.scope_and_content or ''
            row['custodialHistory'] = self.custodial_history or ''
            row['rulesOrConventions'] = self.rules_or_conventions or ''
            row['levelOfDetail'] = self.level_of_detail or ''
            row.update(self.language_of_materials.flatten(version))
            row['languageOfAccessionRecord'] = self.language_of_record or ''
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
        title = self.accession_title or 'No title'
        if self.status:
            title += f' - {self.status.name}'
        return title

    def get_caais_metadata(self):
        """Return a structured dict of the CAAIS metadata elements."""
        data = {
            'section_1': {
                'repository': self.repository,
                'accession_identifier': self.identifiers.accession_identifier().identifier_value,
                'accession_title': self.accession_title,
                'acquisition_method': self.acquisition_method,
                'disposition_authority': self.disposition_authority,
                'other_identifiers': self.identifiers.get_caais_metadata(),
                'archival_units': self.archival_units.get_caais_metadata(),
            },
            'section_2': {
                'source_of_material': self.source_of_materials.get_caais_metadata(),
                'custodial_history': self.custodial_history,
            },
            'section_3': {
                'date_of_material': self.date_of_material,
                'extent_statement': self.extent_statements.get_caais_metadata(),
                'scope_and_content': self.scope_and_content,
                'language_of_materials': self.language_of_materials.get_caais_metadata(),
            },
            'section_4': {
                'storage_location': self.storage_locations.get_caais_metadata(),
                'rights_statement': self.rights.get_caais_metadata(),
                'material_assessment_statement': self.material_assessments.get_caais_metadata(),
                'appraisals_statement': [],
            },
            'section_5': {
                'event_statement': self.events.get_caais_metadata(),
            },
            'section_6': {
                'general_note': self.general_notes.get_caais_metadata(),
            },
            'section_7': {
                'date_of_creation_or_revision': self.date_creation_revisions.get_caais_metadata(),
            },
        }
        if self.status:
            data['section_1']['status'] = self.status.name
        if self.rules_or_conventions:
            data['section_7']['rules_or_conventions'] = self.rules_or_conventions
        if self.level_of_detail:
            data['section_7']['level_of_detail'] = self.level_of_detail
        if self.language_of_record:
            data['section_7']['language_of_accession_record'] = self.language_of_record
        return data

    def update_accession_id(self, accession_id: str, commit: bool = True):
        a_id = self.identifiers.accession_identifier()
        if a_id is not None:
            a_id.identifier_value = accession_id
            if commit:
                a_id.save()


class IdentifierManager(models.Manager):
    ''' Custom identifier related manager
    '''

    def accession_identifier(self):
        ''' Get the first identifier with Accession Identifier or Accession
        Number as the type, or None if an identifier like this does not exist.
        '''
        return self.get_queryset().filter(
            Q(identifier_type__icontains='Accession Identifier') |
            Q(identifier_type__icontains='Accession Number')
        ).first()

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten identifiers in queryset to export them in a CSV.
        '''
        # alternativeIdentifiers were added in AtoM v2.6
        if version in (ExportVersion.ATOM_2_1, ExportVersion.ATOM_2_2, ExportVersion.ATOM_2_3):
            return {}

        if version == ExportVersion.CAAIS_1_0:
            identifiers = self.get_queryset().all()
            return {
                'identifierTypes': '|'.join([
                    id.identifier_type or 'NULL' for id in identifiers
                ]),
                'identifierValues': '|'.join([
                    id.identifier_value or 'NULL' for id in identifiers
                ]),
                'identifierNotes': '|'.join([
                    id.identifier_note or 'NULL' for id in identifiers
                ]),
            }

        if version == ExportVersion.ATOM_2_6:
            identifiers = self.get_queryset().filter(
                Q(identifier_type__icontains='Accession Identifier', _negated=True) &
                Q(identifier_type__icontains='Accession Number', _negated=True)
            ).all()

            return {
                'alternativeIdentifiers': '|'.join([
                    id.identifier_value or 'NULL' for id in identifiers
                ]),
                'alternativeIdentifierTypes': '|'.join([
                    id.identifier_type or 'NULL' for id in identifiers
                ]),
                'alternativeIdentifierNotes': '|'.join([
                    id.identifier_note or 'NULL' for id in identifiers
                ]),
            }

        return {}

    def get_caais_metadata(self):
        identifiers = []
        for identifier in self.get_queryset().filter(
                Q(identifier_type__icontains='Accession Identifier', _negated=True) &
                Q(identifier_type__icontains='Accession Number', _negated=True)
        ).all():
            identifiers.append({
                'other_identifier_type': identifier.identifier_type,
                'other_identifier_value': identifier.identifier_value,
                'other_identifier_note': identifier.identifier_note,
            })
        return identifiers


class Identifier(models.Model):
    ''' 1.2 Identifiers (Repeatable field)
    '''

    objects = IdentifierManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='identifiers')
    identifier_type = models.CharField(max_length=128, null=False, help_text=gettext(
        "Record the identifier type in accordance with a controlled vocabulary "
        "maintained by the repository"
    ))
    identifier_value = models.CharField(max_length=128, null=False, help_text=gettext(
        "Record the other identifier value as received or generated by the "
        "repository"
    ))
    identifier_note = models.TextField(null=True, help_text=gettext(
        "Record any additional information that clarifies the purpose, use or "
        "generation of the identifier."
    ))

    def __str__(self):
        return f'{self.identifier_value} ({self.identifier_type})'


class ArchivalUnitManager(models.Manager):
    ''' Custom archival unit manager
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten archival units in queryset to export them in a CSV.
        '''
        # No equivalent for archival unit in AtoM
        if version != ExportVersion.CAAIS_1_0:
            return {}

        # Don't bother including NULL for empty archival units, just skip them
        units = self.get_queryset().exclude(
            Q(archival_unit__exact='') |
            Q(archival_unit__isnull=True)
        ).values_list('archival_unit', flat=True)

        return {'archivalUnit': '|'.join(units)}

    def get_caais_metadata(self):
        units = []
        for unit in self.get_queryset().all():
            units.append({
                'archival_unit': unit.archival_unit,
            })
        return units


class ArchivalUnit(models.Model):
    ''' 1.4 Archival Unit (Repeatable field)
    '''

    objects = ArchivalUnitManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='archival_units')
    archival_unit = models.TextField(null=False, help_text=gettext(
        "Record the reference code and/or title of the archival unit to which the accession belongs."
    ))

    def __str__(self):
        return f'Archival Unit #{self.id}'


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
    '''
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = gettext('Source roles')
        verbose_name = gettext('Source role')
SourceRole._meta.get_field('name').help_text = gettext(
    "Record the source role (when known) in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class SourceConfidentiality(AbstractTerm):
    ''' 2.1.6 Source Confidentiality (Non-repeatable)
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


class SourceOfMaterialManager(models.Manager):
    ''' Custom source of material manager
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten source of material info in queryset to export them in a CSV.
        '''
        if self.get_queryset().count() == 0:
            return {}

        types = []
        names = []
        contact_persons = []
        job_titles = []
        street_addresses = []
        cities = []
        regions = []
        postal_codes = []
        countries = []
        phone_numbers = []
        emails = []
        roles = []
        notes = []
        confidentialities = []

        is_atom = ExportVersion.is_atom(version)

        def get_source_attr(src, attrs):
            value = get_nested_attr(src, attrs)
            if value:
                return value
            return '' if is_atom else 'NULL'

        for source in self.get_queryset().all():
            get_field = partial(get_source_attr, source)

            types.append(get_field('source_type,name'))
            names.append(get_field('source_name'))
            contact_persons.append(get_field('contact_name'))
            job_titles.append(get_field('job_title'))

            # Join address line 1 and 2
            if source.address_line_1 and source.address_line_2:
                street_addresses.append(', '.join([
                    source.address_line_1,
                    source.address_line_2,
                ]))
            elif source.address_line_1:
                street_addresses.append(source.address_line_1)
            elif source.address_line_2:
                street_addresses.append(source.address_line_2)
            else:
                street_addresses.append('' if is_atom else 'NULL')

            cities.append(get_field('city'))
            regions.append(get_field('region'))
            postal_codes.append(get_field('postal_or_zip_code'))
            countries.append(get_field('country,name'))
            phone_numbers.append(get_field('phone_number'))
            emails.append(get_field('email_address'))
            roles.append(get_field('source_role,name'))
            notes.append(get_field('source_note'))
            confidentialities.append(get_field('source_confidentiality,name'))

            # AtoM can only handle one source!
            if is_atom:
                break

        flat = {}

        if not is_atom:
            flat['sourceType'] = '|'.join(types)
            flat['sourceName'] = '|'.join(names)
            flat['sourceContactPerson'] = '|'.join(contact_persons)
            flat['sourceJobTitle'] = '|'.join(job_titles)
            flat['sourceStreetAddress'] = '|'.join(street_addresses)
            flat['sourceCity'] = '|'.join(cities)
            flat['sourceRegion'] = '|'.join(regions)
            flat['sourcePostalCode'] = '|'.join(postal_codes)
            flat['sourceCountry'] = '|'.join(countries)
            flat['sourcePhoneNumber'] = '|'.join(phone_numbers)
            flat['sourceEmail'] = '|'.join(emails)
            flat['sourceRole'] = '|'.join(roles)
            flat['sourceNote'] = '|'.join(notes)
            flat['sourceConfidentiality'] = '|'.join(confidentialities)

        else:
            flat = {}

            note = notes[0]
            role = roles[0]
            type_ = types[0]
            confidentiality = confidentialities[0]

            # donorNote added in AtoM 2.6
            # donorContactPerson added in AtoM 2.6
            if version == ExportVersion.ATOM_2_6 and any((note, role, type_, confidentiality)):
                donor_narrative = []
                if type_:
                    if type_[0].lower() in ('a', 'e', 'i', 'o', 'u'):
                        donor_narrative.append(f'The donor is an {type_}')
                    else:
                        donor_narrative.append(f'The donor is a {type_}')
                if role:
                    donor_narrative.append((
                        'The donor\'s relationship to the records is: '
                        f'{role}'
                    ))
                if confidentiality:
                    donor_narrative.append((
                        'The donor\'s confidentiality has been noted as: '
                        f'{confidentiality}'
                    ))
                if note:
                    donor_narrative.append(note)
                flat['donorNote'] = '. '.join(donor_narrative)
                flat['donorContactPerson'] = contact_persons[0]

            flat['donorName'] = names[0]
            flat['donorStreetAddress'] = street_addresses[0]
            flat['donorCity'] = cities[0]
            flat['donorRegion'] = regions[0]
            flat['donorPostalCode'] = postal_codes[0]
            flat['donorCountry'] = countries[0]
            flat['donorTelephone'] = phone_numbers[0]
            flat['donorEmail'] = emails[0]

        return flat

    def get_caais_metadata(self):
        sources = []
        for source in self.get_queryset().all():
            sources.append({
                'source_type': str(source.source_type.name),
                'source_name': source.source_name,
                'source_role': str(source.source_role.name),
                'source_contact_information': {
                    'contact_name': source.contact_name,
                    'job_title': source.job_title,
                    'phone_number': source.phone_number,
                    'email': source.email_address,
                    'address_line_1': source.address_line_1,
                    'address_line_2': source.address_line_2,
                    'city': source.city,
                    'province_or_state': source.region,
                    'postal_or_zip_code': source.postal_or_zip_code,
                    'country': source.country,
                },
                'source_note': source.source_note,
            })
        return sources


class SourceOfMaterial(models.Model):
    ''' 2.1 Source of Material (Repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Sources of material')
        verbose_name = gettext('Source of material')

    objects = SourceOfMaterialManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='source_of_materials')

    source_type = models.ForeignKey(SourceType, on_delete=models.SET_NULL,
                                    null=True, related_name='source_of_materials')

    source_name = models.CharField(max_length=256, null=False, default='', help_text=gettext(
        "Record the source name in accordance with the repository's "
        "descriptive standard"
    ))

    source_role = models.ForeignKey(SourceRole, on_delete=models.SET_NULL,
                                    null=True, related_name='source_of_materials')

    source_confidentiality = models.ForeignKey(SourceConfidentiality, on_delete=models.SET_NULL,
                                               null=True, related_name='source_of_materials')

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

    source_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information about the source of the accessioned "
        "materials. If the source performed the role for only a specific "
        "period of time (e.g. was a custodian for several years), record the "
        "dates in this element"
    ))

    def __str__(self):
        return f'{self.source_name} (Phone: {self.phone_number})'


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
            quantities.append(get_field('quantity_and_type_of_units'))
            extent_notes.append(get_field('extent_note'))

        if not is_atom:
            return {
                'extentStatementType': '|'.join(extent_types),
                'quantityAndTypeOfUnits': '|'.join(quantities),
                'extentStatementNote': '|'.join(extent_notes),
            }
        else:
            return {
                'receivedExtentUnits': '|'.join(quantities)
            }

    def get_caais_metadata(self):
        extents = []
        for extent in self.get_queryset().all():
            extents.append({
                'extent_statement_type': str(extent.extent_type.name),
                'quantity_and_type_of_units': extent.quantity_and_type_of_units,
                'extent_statement_note': extent.extent_note,
            })
        return extents


class ExtentStatement(models.Model):
    ''' 3.2 Extent Statement (repeatable)
    '''

    class Meta:
        verbose_name = gettext('Extent statement')
        verbose_name_plural = gettext('Extent statements')

    objects = ExtentStatementManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='extent_statements')

    extent_type = models.ForeignKey(ExtentType, on_delete=models.SET_NULL,
                                    null=True, related_name='extent_statements')

    quantity_and_type_of_units = models.CharField(max_length=256, null=False, blank=False,
                                                  default=gettext('Not specified'),
                                                  help_text=gettext((
                                                        "Record the number and unit of measure expressing the quantity "
                                                        "of the extent (e.g., 5 files, totalling 2.5MB)"
                                                    )))

    extent_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record additional information related to the number and type of units "
        "received, retained, or removed not otherwise recorded"
    ))

    def __str__(self):
        return f'Extent Statement #{self.id}'


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
            values.append(rights.rights_value or 'NULL')
            notes.append(rights.rights_note or 'NULL')

        return {
            'rightsStatementType': '|'.join(types),
            'rightsStatementValue': '|'.join(values),
            'rightsStatementNote': '|'.join(notes),
        }

    def get_caais_metadata(self):
        rights = []
        for right in self.get_queryset().all():
            rights.append({
                'rights_statement_type': str(right.rights_type.name),
                'rights_statement_value': right.rights_value,
                'rights_statement_note': right.rights_note,
            })
        return rights


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
