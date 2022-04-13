''' Models describing the Canadian Archival Accession Information Standard v1.0:

http://archivescanada.ca/uploads/files/Documents/CAAIS_2019May15_EN.pdf
'''
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext

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

        else:
            row['title'] = self.accession_title or 'No title'
            row['acquisitionType'] = self.acquisition_method or ''

            accession_identifier = self.identifiers.accession_identifier()
            if accession_identifier is not None:
                row['accessionNumber'] = accession_identifier.identifier_value
            else:
                row['accessionNumber'] = ''

        row.update(self.identifiers.flatten(version))
        row.update(self.archival_units.flatten(version))
        row.update(self.disposition_authorities.flatten(version))
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
        ).all()

        return {
            'archivalUnit': '|'.join([
                u.archival_unit for u in units
            ])
        }


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


class DispositionAuthorityManager(models.Manager):
    ''' Custom disposition authority manager
    '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0):
        ''' Flatten archival units in queryset to export them in a CSV.
        '''
        # No equivalent for disposition authority in AtoM
        if version != ExportVersion.CAAIS_1_0:
            return {}

        # Don't bother including NULL for empty disposition authority, just skip it
        authorities = self.get_queryset().exclude(
            Q(disposition_authority__exact='') |
            Q(disposition_authority__isnull=True)
        ).all()

        return {
            'dispositionAuthority': '|'.join([
                d.disposition_authority for d in authorities
            ])
        }


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
