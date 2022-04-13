''' Models describing the Canadian Archival Accession Information Standard v1.0:

http://archivescanada.ca/uploads/files/Documents/CAAIS_2019May15_EN.pdf
'''
from functools import partial

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext

from django_countries.fields import CountryField

from caais.dates import EventDateParser, UnknownDateFormat
from caais.export import ExportVersion


class Status(models.Model):
    ''' 1.7 Status (Non-repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Accession statuses')
        verbose_name = gettext('Accession status')

    status = models.CharField(max_length=128, null=True, help_text=gettext(
        "This element is intended to support the tracking of a material "
        "through an accession procedure that has clearly defined, successive "
        "phases"
    ))

    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.status


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
            row['status'] = self.status.status if self.status else ''
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
        return row

    def __str__(self):
        title = self.accession_title or 'No title'
        if self.status:
            title += f' - {self.status.status}'
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


class SourceType(models.Model):
    ''' 2.1.1 Source Type (Non-repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Source types')
        verbose_name = gettext('Source type')

    source_type = models.CharField(max_length=128, null=True, help_text=gettext(
        "Record the source in accordance with a controlled vocabulary "
        "maintained by the repository"
    ))

    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.source_type


class SourceRole(models.Model):
    ''' 2.1.4 Source Role (Non-repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Source roles')
        verbose_name = gettext('Source role')

    source_role = models.CharField(max_length=128, null=True, help_text=gettext(
        "Record the source role (when known) in accordance with a controlled "
        "vocabulary maintained by the repository"
    ))

    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.source_role


class SourceConfidentiality(models.Model):
    ''' 2.1.6 Source Confidentiality (Non-repeatable)
    '''

    class Meta:
        verbose_name_plural = gettext('Source confidentialities')
        verbose_name = gettext('Source confidentiality')

    source_confidentiality = models.CharField(max_length=128, null=True, help_text=gettext(
        "Use this element to identify source statements or source information "
        "that is for internal use only by the repository. Repositories should "
        "develop a controlled vocabulary with terms that can be  translated "
        "into clear rules for handling source information"
    ))

    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.source_confidentiality


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
            obj = src
            attrs = attrs.split(',')
            for attr in attrs:
                try:
                    obj = getattr(obj, attr)
                except AttributeError:
                    return '' if is_atom else 'NULL'
            if obj:
                return str(obj)
            return '' if is_atom else 'NULL'

        for source in self.get_queryset().all():
            get_field = partial(get_source_attr, source)

            types.append(get_field('source_type,source_type'))
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
            roles.append(get_field('source_role,source_role'))
            notes.append(get_field('source_note'))
            confidentialities.append(get_field('source_confidentiality,source_confidentiality'))

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
