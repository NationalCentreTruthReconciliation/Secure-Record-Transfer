from abc import ABC, abstractmethod
import re

from django.db import models
from django.db.models import Q, CharField, Value, Case, When, Value, F
from django.db.models.functions import Concat

from caais.db import DefaultConcat, GroupConcat, CharFieldOrDefault
from caais.export import ExportVersion


PUNCTUATION_END = re.compile(r'(?:\?|!|\.|,|;)\s*$')


class MetadataManager(models.Manager):
    def flatten(self, version=ExportVersion.CAAIS_1_0) -> dict:
        ''' Convert this model and all related models into a flat dictionary
        suitable to be written to a CSV or used as the metadata fields for a
        BagIt bag.
        '''
        return [
            metadata.create_flat_representation(version) for metadata in self.get_queryset()
        ]


class CaaisModelManager(models.Manager, ABC):
    ''' Custom manager for CAAIS models that require the flatten() function.
    '''

    @abstractmethod
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Flatten metadata to be used for AtoM
        '''

    @abstractmethod
    def flatten_caais(self, version: ExportVersion) -> dict:
        ''' Flatten metadata to be used for CAAIS
        '''

    def flatten(self, version: ExportVersion = ExportVersion.CAAIS_1_0) -> dict:
        ''' Flatten metadata to be used in BagIt metadata or CSV file
        '''
        data = None
        if version == ExportVersion.CAAIS_1_0:
            data = self.flatten_caais(version)
        else:
            data = self.flatten_atom(version)
        if not data or not any(data.values()):
            return {}
        return data


class IdentifierManager(CaaisModelManager):
    def accession_identifier(self):
        ''' Get the first identifier with Accession Identifier or Accession
        Number as the type, or None if an identifier like this does not exist.
        '''
        return self.get_queryset().filter(
            Q(identifier_type__icontains='Accession Identifier') |
            Q(identifier_type__icontains='Accession Number')
        ).first()

    def flatten_atom(self, version: ExportVersion) -> dict:
        # alternativeIdentifiers were added in AtoM v2.6
        if version in (ExportVersion.ATOM_2_1, ExportVersion.ATOM_2_2, ExportVersion.ATOM_2_3):
            return {}

        return self.get_queryset().filter(
            ~Q(identifier_type__icontains='Accession Identifier') &
            ~Q(identifier_type__icontains='Accession Number')
        ).aggregate(
            alternativeIdentifiers=DefaultConcat(
                CharFieldOrDefault('identifier_value')
            ),
            alternativeIdentifierTypes=DefaultConcat(
                CharFieldOrDefault('identifier_type')
            ),
            alternativeIdentifierNotes=DefaultConcat(
                CharFieldOrDefault('identifier_note')
            )
        )

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            identifierTypes=DefaultConcat(
                CharFieldOrDefault('identifier_type')
            ),
            identifierValues=DefaultConcat(
                CharFieldOrDefault('identifier_value')
            ),
            identifierNotes=DefaultConcat(
                CharFieldOrDefault('identifier_note')
            ),
        )


class ArchivalUnitManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # No equivalent for archival unit in AtoM
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            archivalUnits=DefaultConcat('archival_unit')
        )


class DispositionAuthorityManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # No equivalent for disposition authority in AtoM
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            dispositionAuthorities=DefaultConcat('disposition_authority')
        )


class SourceOfMaterialManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # AtoM only supports one "donor"
        first_donor = self.get_queryset().order_by('id').first()

        if not first_donor:
            return {}

        address = ', '.join(l for l in [
            first_donor.address_line_1,
            first_donor.address_line_2,
        ] if l)

        flat = {
            'donorName': first_donor.source_name or '',
            'donorStreetAddress': address,
            'donorCity': first_donor.city or '',
            'donorRegion': first_donor.region or '',
            'donorPostalCode': first_donor.postal_or_zip_code or '',
            'donorCountry': first_donor.country.code if first_donor.country else '',
            'donorTelephone': first_donor.phone_number or '',
            'donorEmail': first_donor.email_address or '',
        }

        # donorNote added in AtoM 2.6
        # donorFax added in AtoM 2.6
        # donorContactPerson added in AtoM 2.6
        if version == ExportVersion.ATOM_2_6:
            flat['donorFax'] = ''
            flat['donorContactPerson'] = first_donor.contact_name

            note = first_donor.source_note
            role = first_donor.source_role.name if first_donor.source_role else ''
            type_ = first_donor.source_type.name if first_donor.source_type else ''
            confidentiality = first_donor.source_confidentiality.name if first_donor.source_confidentiality else ''

            # Create narrative for donor note
            if any([note, role, type_, confidentiality]):
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
        sources = self.get_queryset()
        return {
            # Countries don't behave in the query, so concatenate them separately
            'sourceCountry': '|'.join([
                source.country.code if source.country else 'NULL' \
                for source in sources]
            ),
            **sources.annotate(
                # Join address line 1 and address line 2
                address=Case(
                    When((~Q(address_line_1='')) & (~Q(address_line_2='')),
                         then=Concat(
                            F('address_line_1'),
                            Value(', '),
                            F('address_line_2')
                        )
                    ),
                    When(~Q(address_line_1=''), then=F('address_line_1')),
                    When(~Q(address_line_2=''), then=F('address_line_2')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )
            ).aggregate(
                sourceType=DefaultConcat(Case(
                    When(Q(source_type__isnull=False), then=F('source_type__name')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )),
                sourceName=DefaultConcat(
                    CharFieldOrDefault('source_name')
                ),
                sourceContactPerson=DefaultConcat(
                    CharFieldOrDefault(field_name='contact_name')
                ),
                sourceJobTitle=DefaultConcat(
                    CharFieldOrDefault(field_name='job_title')
                ),
                sourceOrganization=DefaultConcat(
                    CharFieldOrDefault(field_name='organization')
                ),
                sourceStreetAddress=DefaultConcat(
                    # Address is already sanitized
                    F('address'),
                ),
                sourceCity=DefaultConcat(
                    CharFieldOrDefault(field_name='city')
                ),
                sourceRegion=DefaultConcat(
                    CharFieldOrDefault(field_name='region')
                ),
                sourcePostalCode=DefaultConcat(
                    CharFieldOrDefault(field_name='postal_or_zip_code')
                ),
                sourcePhoneNumber=DefaultConcat(
                    CharFieldOrDefault(field_name='phone_number')
                ),
                sourceEmail=DefaultConcat(
                    CharFieldOrDefault(field_name='email_address')
                ),
                sourceRole=DefaultConcat(Case(
                    When(Q(source_role__isnull=False), then=F('source_role__name')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )),
                sourceNote=DefaultConcat(
                    CharFieldOrDefault(field_name='source_note')
                ),
                sourceConfidentiality=DefaultConcat(Case(
                    When(Q(source_confidentiality__isnull=False), then=F('source_confidentiality__name')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )),
            )
        }


class PreliminaryCustodialHistoryManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Include single custodial history if there is only one, otherwise
        create a bullet point list of all received extents.
        '''
        histories = self.get_queryset()\
                        .values_list('preliminary_custodial_history', flat=True)

        if len(histories) == 1:
            archival_history = histories[0]
        elif len(histories) > 1:
            archival_history = '\n'.join(f'* {h}' for h in histories)
        else:
            archival_history = ''

        if archival_history:
            return {'archivalHistory': archival_history}
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            preliminaryCustodialHistory=DefaultConcat('preliminary_custodial_history')
        )


class ExtentStatementManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Include single extent if there is only one, otherwise create a
        bullet point list of all received extents.
        '''
        extents = self.get_queryset()\
                      .exclude(quantity_and_unit_of_measure='')\
                      .values_list('quantity_and_unit_of_measure', flat=True)

        if len(extents) == 1:
            received_extent = extents[0]
        elif len(extents) > 1:
            received_extent = '\n'.join(f'* {e}' for e in extents)
        else:
            received_extent = ''

        if received_extent:
            return {'receivedExtentUnits': received_extent}
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            extentTypes=DefaultConcat(Case(
                When(Q(extent_type__isnull=False), then=F('extent_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            quantityAndUnitOfMeasure=DefaultConcat(
                CharFieldOrDefault(field_name='quantity_and_unit_of_measure'),
            ),
            contentTypes=DefaultConcat(Case(
                When(Q(content_type__isnull=False), then=F('content_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            carrierTypes=DefaultConcat(Case(
                When(Q(carrier_type__isnull=False), then=F('carrier_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            extentNotes=DefaultConcat(
                CharFieldOrDefault(field_name='extent_note')
            ),
        )


class PreliminaryScopeAndContentManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            scopeAndContent=GroupConcat('preliminary_scope_and_content', separator='; ')
        )

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            preliminaryScopeAndContent=DefaultConcat('preliminary_scope_and_content'),
        )


class LanguageOfMaterialManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        queryset = self.get_queryset()
        if queryset.count() == 0:
            return {}
        return self.get_queryset().aggregate(
            scopeAndContent=Concat(
                Value('Language(s) of materials: '),
                GroupConcat('language_of_material', separator='; '),
            )
        )

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            languageOfMaterials=DefaultConcat('language_of_material')
        )


class StorageLocationManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Include single location if there is only one, otherwise create a
        bullet point list of all location values.
        '''
        locations = self.get_queryset()\
                      .values_list('storage_location', flat=True)

        if len(locations) == 1:
            location = locations[0]
        elif len(locations) > 1:
            location = '\n'.join(f'* {l}' for l in locations)
        else:
            location = ''

        if location:
            return {'locationInformation': location}
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            storageLocation=DefaultConcat('storage_location')
        )


class RightsManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # There is no equivalent field in AtoM for rights
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            rightsTypes=DefaultConcat(Case(
                When(Q(rights_type__isnull=False), then=F('rights_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            rightsValues=DefaultConcat(
                CharFieldOrDefault('rights_value'),
            ),
            rightsNotes=DefaultConcat(
                CharFieldOrDefault('rights_note'),
            ),
        )


class PreservationRequirementsManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Include first value + note if there is only one, otherwise include
        every value + note in a bullet point list.
        '''
        processing_notes = []
        for req in self.get_queryset():
            value = req.preservation_requirements_value
            note = req.preservation_requirements_note

            if value and note:
                if not PUNCTUATION_END.search(value):
                    list_item = f'{value}. {note}'
                else:
                    list_item = f'{value} {note}'
            elif value:
                list_item = value
            elif note:
                list_item = note
            else:
                list_item = ''

            if list_item:
                processing_notes.append(list_item)

        if len(processing_notes) == 1:
            note = processing_notes[0]
        elif len(processing_notes) > 1:
            note = '\n'.join(f'* {n}' for n in processing_notes)
        else:
            note = ''

        if note:
            return {'processingNotes': note}
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            preservationRequirementsTypes=DefaultConcat(Case(
                When(Q(preservation_requirements_type__isnull=False), then=F('preservation_requirements_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            preservationRequirementsValues=DefaultConcat(
                CharFieldOrDefault('preservation_requirements_value'),
            ),
            preservationRequirementsNotes=DefaultConcat(
                CharFieldOrDefault('preservation_requirements_note'),
            ),
        )


class AppraisalManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        ''' Include single appraisal value + note if there is only one,
        otherwise create a bullet point list of all appraisals' value + note.
        '''
        appraisals = []
        for app in self.get_queryset():
            value = app.appraisal_value
            note = app.appraisal_note

            if value and note:
                if not PUNCTUATION_END.search(value):
                    list_item = f'{value}. {note}'
                else:
                    list_item = f'{value} {note}'
            elif value:
                list_item = value
            elif note:
                list_item = note
            else:
                list_item = ''

            if list_item:
                appraisals.append(list_item)

        if len(appraisals) == 1:
            appraisal = appraisals[0]
        elif len(appraisals) > 1:
            appraisal = '\n'.join(f'* {n}' for n in appraisals)
        else:
            appraisal = ''

        if appraisal:
            return {'appraisal': appraisal}
        return {}


    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            appraisalTypes=DefaultConcat(Case(
                When(Q(appraisal_type__isnull=False), then=F('appraisal_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            appraisalValues=DefaultConcat(
                CharFieldOrDefault('appraisal_value'),
            ),
            appraisalNotes=DefaultConcat(
                CharFieldOrDefault('appraisal_note'),
            ),
        )


class AssociatedDocumentationManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # There is no equivalent field in AtoM for associated documentation
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            associatedDocumentationTypes=DefaultConcat(Case(
                When(Q(associated_documentation_type__isnull=False), then=F('associated_documentation_type__name')),
                default=Value('NULL'),
                output_field=CharField(),
            )),
            associatedDocumentationTitles=DefaultConcat(
                CharFieldOrDefault('associated_documentation_title'),
            ),
            associatedDocumentationNotes=DefaultConcat(
                CharFieldOrDefault('associated_documentation_note'),
            )
        )


class EventManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # There is no equivalent field in AtoM for non-Creation events
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        events = self.get_queryset()
        return {
            # We use Python to convert dates to strings
            'eventDates': '|'.join(
                e.event_date.strftime(r'%Y-%m-%d') if e.event_date else 'NULL' \
                for e in events
            ),
            # And the database is used to do the rest of the work
            **events.aggregate(
                eventTypes=DefaultConcat(Case(
                    When(Q(event_type__isnull=False), then=F('event_type__name')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )),
                eventAgents=DefaultConcat(
                    CharFieldOrDefault('event_agent'),
                ),
                eventNotes=DefaultConcat(
                    CharFieldOrDefault('event_note'),
                )
            )
        }


class GeneralNoteManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # There is no equivalent for general notes in AtoM
        return {}

    def flatten_caais(self, version: ExportVersion) -> dict:
        return self.get_queryset().aggregate(
            generalNotes=DefaultConcat('general_note')
        )


class DateOfCreationOrRevisionManager(CaaisModelManager):
    def flatten_atom(self, version: ExportVersion) -> dict:
        # Take only the first date, and treat as a date of acquisition
        date = self.get_queryset().first()
        if not date:
            return {}
        return {
            'acquisitionDate': date.creation_or_revision_date.strftime(r'%Y-%m-%d')
        }

    def flatten_caais(self, version: ExportVersion) -> dict:
        dates = self.get_queryset()

        return {
            # We use Python to convert dates to strings
            'creationOrRevisionDates': '|'.join(
                d.creation_or_revision_date.strftime(r'%Y-%m-%d') \
                if d.creation_or_revision_date else 'NULL' \
                for d in dates
            ),
            **dates.aggregate(
                creationOrRevisionTypes=DefaultConcat(Case(
                    When(Q(creation_or_revision_type__isnull=False), then=F('creation_or_revision_type__name')),
                    default=Value('NULL'),
                    output_field=CharField(),
                )),
                creationOrRevisionAgents=DefaultConcat(
                    CharFieldOrDefault('creation_or_revision_agent')
                ),
                creationOrRevisionNotes=DefaultConcat(
                    CharFieldOrDefault('creation_or_revision_note')
                ),
            )
        }
