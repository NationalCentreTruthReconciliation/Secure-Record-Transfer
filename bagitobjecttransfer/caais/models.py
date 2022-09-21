''' Models describing the Canadian Archival Accession Information Standard v1.0:

http://archivescanada.ca/uploads/files/Documents/CAAIS_2019May15_EN.pdf
'''
from functools import partial
from typing import Union, Iterable

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
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
    '''

    class Meta:
        abstract = True

    objects = TermManager()

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
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True,
                               related_name='metadatas')
    date_of_material = models.CharField(max_length=128, null=True, help_text=gettext(
        "Provide a preliminary estimate of the date range or explicitly "
        "indicate if not it has yet been determined"
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

        else:
            row['title'] = self.accession_title or 'No title'
            row['acquisitionType'] = self.acquisition_method or ''

            accession_identifier = self.identifiers.accession_identifier()
            if accession_identifier is not None:
                row['accessionNumber'] = accession_identifier.identifier_value
            else:
                row['accessionNumber'] = ''

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

        row.update(self.identifiers.flatten(version))
        row.update(self.archival_units.flatten(version))
        row.update(self.disposition_authorities.flatten(version))
        row.update(self.source_of_materials.flatten(version))
        row.update(self.preliminary_custodial_histories.flatten(version))
        row.update(self.extent_statements.flatten(version))

        scope_updates = self.preliminary_scope_and_contents.flatten(version)
        language_updates = self.language_of_materials.flatten(version)

        if 'scopeAndContent' in scope_updates and language_updates:
            combined_updates = {
                'scopeAndContent': '. '.join([
                    scope_updates['scopeAndContent'].rstrip('. '),
                    language_updates['scopeAndContent'].rstrip('. '),
                ])
            }
            row.update(combined_updates)
        else:
            row.update(scope_updates)
            row.update(language_updates)

        row.update(self.storage_locations.flatten(version))
        row.update(self.rights.flatten(version))
        return row

    def __str__(self):
        title = self.accession_title or 'No title'
        if self.status:
            title += f' - {self.status.name}'
        return title


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
            accession_identifier = self.accession_identifier()

            if accession_identifier:
                identifiers = self.get_queryset().all().exclude(id=accession_identifier.id)
            else:
                identifiers = self.get_queryset().all()

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
    ''' Custom arhival unit manager
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


class ArchivalUnit(models.Model):
    ''' 1.4 Archival Unit (Repeatable field)
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


class DispositionAuthorityManager(models.Manager):
    ''' Custom disposition authority manager
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten disposition authorities in queryset to export them in a CSV.
        '''
        # No equivalent for disposition authority in AtoM
        if version != ExportVersion.CAAIS_1_0:
            return {}

        # Don't bother including NULL for empty disposition authority, just skip it
        authorities = self.get_queryset().exclude(
            Q(disposition_authority__exact='') |
            Q(disposition_authority__isnull=True)
        ).values_list('disposition_authority', flat=True)

        return {'dispositionAuthority': '|'.join(authorities)}


class DispositionAuthority(models.Model):
    ''' 1.6 - Disposition Authority (Repeatable field)
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


class PreliminaryCustodialHistoryManager(models.Manager):
    ''' Custom manager for preliminary custodial histories
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten custodial histories in queryset to export them in a CSV.
        '''
        histories = self.get_queryset().exclude(
            Q(preliminary_custodial_history__exact='') |
            Q(preliminary_custodial_history__isnull=True)
        ).values_list('preliminary_custodial_history', flat=True)

        if version == ExportVersion.CAAIS_1_0:
            return {'preliminaryCustodialHistory': '|'.join(histories)}
        return {'archivalHistory': '; '.join(histories)}


class PreliminaryCustodialHistory(models.Model):
    ''' 2.2 Preliminary Custodial History
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
ContentType._meta.get_field('name').help_text = mark_safe(gettext(
    "Record the type of material contained in the units measured, i.e., the "
    "<b>genre</b> of the material"
))


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
                'quantityAndUnitOfMeasure': '|'.join(quantities),
                'contentType': '|'.join(content_types),
                'carrierType': '|'.join(carrier_types),
                'extentNote': '|'.join(extent_notes),
            }
        else:
            return {
                'receivedExtentUnits': '|'.join(quantities)
            }


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

    quantity_and_unit_of_measure = models.CharField(
        max_length=256, null=False, blank=False, default=gettext('Not specified'),
        help_text=gettext((
        "Record the number and unit of measure expressing the quantity of the "
        "extent (e.g., 5 files, totalling 2.5MB)"
    )))

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL,
                                     null=True, related_name='extent_statements')

    carrier_type = models.ForeignKey(CarrierType, on_delete=models.SET_NULL,
                                     null=True, related_name='extent_statements')

    extent_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record additional information related to the number and type of units "
        "received, retained, or removed not otherwise recorded"
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

        for rights in self.get_queryset():
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


class PreservationRequirementType(AbstractTerm):
    """ 4.3.1 Preservation Requirement Type (Repeatable)
    """
    class Meta(AbstractTerm.Meta):
        verbose_name_plural = 'Preservation Requirement Types'
        verbose_name = 'Preservation Requirement Type'

PreservationRequirementType._meta.get_field('name').help_text = gettext(
    "Record the preservation requirement type in accordance with a controlled "
    "vocabulary maintained by the repository"
)


class PreservationRequirementManager(models.Manager):
    """ Custom manager for preservation requirements
    """

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        """ Convert preservation in queryset to a flat dictionary
        """
        # There is no equivalent field in AtoM for rights
        if self.get_queryset().count() == 0:
            return {}

        types = []
        values = []
        notes = []

        for assessments in self.get_queryset():
            if assessments.rights_type and assessments.rights_type.name:
                types.append(str(assessments.rights_type.name))
            else:
                types.append('NULL')
            if assessments.rights_value:
                values.append(assessments.rights_value)
            else:
                values.append('NULL')
            if assessments.rights_note:
                notes.append(assessments.rights_note)
            else:
                notes.append('NULL')

        return {
            'preservationRequirementType': '|'.join(types),
            'preservationRequirementValue': '|'.join(values),
            'preservationRequirementNote': '|'.join(notes),
        }


class PreservationRequirement(models.Model):
    """ 4.3 Preservation Requirement (Repeatable)
    """

    class Meta:
        verbose_name_plural = 'Preservation Requirements'
        verbose_name = 'Preservation Requirement'

    objects = PreservationRequirementManager()

    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE, null=False,
                                 related_name='preservation_requirement')

    requirement_type = models.ForeignKey(PreservationRequirementType, on_delete=models.SET_NULL, null=True,
                                         related_name='preservation_requirement_type')

    requirement_value = models.TextField(blank=True, default='', help_text=gettext(
        "Record information about the assessment of the material with respect to its physical "
        "condition, dependencies, processing or access."
    ))

    requirement_note = models.TextField(blank=True, default='', help_text=gettext(
        "Record any other information relevant to the long-term preservation of the material."
    ))

    def __str__(self):
        return f'Preservation Requirement #{self.id}'
