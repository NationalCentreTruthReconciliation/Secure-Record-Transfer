from enum import Enum, auto


class ExportVersion(Enum):
    ''' Defines the different types and versions of CSVs that can be exported.
    '''

    CAAIS_1_0 = auto()
    ATOM_2_6 = auto()
    ATOM_2_3 = auto()
    ATOM_2_2 = auto()
    ATOM_2_1 = auto()

    @property
    def fieldnames(self):
        ''' Get CSV column names for the specific version.
        '''

        if self == ExportVersion.CAAIS_1_0:
            # TODO: Incomplete! Only contains section 1
            return [
                'repository',
                'identifierTypes',
                'identifierValues',
                'identifierNotes',
                'accessionTitle',
                'archivalUnit',
                'acquisitionMethod',
                'dispositionAuthority',
                'status',
            ]

        if self == ExportVersion.ATOM_2_6:
            return [
                'accessionNumber',
                'alternativeIdentifiers',
                'alternativeIdentifierTypes',
                'alternativeIdentifierNotes',
                'acquisitionDate',
                'sourceOfAcquisition',
                'locationInformation',
                'acquisitionType',
                'resourceType',
                'title',
                'archivalHistory',
                'scopeAndContent',
                'appraisal',
                'physicalCondition',
                'receivedExtentUnits',
                'processingStatus',
                'processingPriority',
                'processingNotes',
                'physicalObjectName',
                'physicalObjectLocation',
                'physicalObjectType',
                'donorName',
                'donorStreetAddress',
                'donorCity',
                'donorRegion',
                'donorCountry',
                'donorPostalCode',
                'donorTelephone',
                'donorFax',
                'donorEmail',
                'donorNote',
                'donorContactPerson',
                'creators',
                'eventTypes',
                'eventDates',
                'eventStartDates',
                'eventEndDates',
                'culture',
            ]

        if self == ExportVersion.ATOM_2_3:
            return [
                'accessionNumber',
                'acquisitionDate',
                'sourceOfAcquisition',
                'locationInformation',
                'acquisitionType',
                'resourceType',
                'title',
                'archivalHistory',
                'scopeAndContent',
                'appraisal',
                'physicalCondition',
                'receivedExtentUnits',
                'processingStatus',
                'processingPriority',
                'processingNotes',
                'donorName',
                'donorStreetAddress',
                'donorCity',
                'donorRegion',
                'donorCountry',
                'donorPostalCode',
                'donorTelephone',
                'donorEmail',
                'creators',
                'eventTypes',
                'eventDates',
                'eventStartDates',
                'eventEndDates',
                'culture',
            ]

        if self == ExportVersion.ATOM_2_2:
            return [
                'accessionNumber',
                'acquisitionDate',
                'sourceOfAcquisition',
                'locationInformation',
                'acquisitionType',
                'resourceType',
                'title',
                'creators',
                'creationDates',
                'creationDatesStart',
                'creationDatesEnd',
                'creationDatesType',
                'qubitParentSlug',
                'archivalHistory',
                'scopeAndContent',
                'appraisal',
                'physicalCondition',
                'receivedExtentUnits',
                'processingStatus',
                'processingPriority',
                'processingNotes',
                'donorName',
                'donorStreetAddress',
                'donorCity',
                'donorRegion',
                'donorCountry',
                'donorPostalCode',
                'donorTelephone',
                'donorEmail',
                'culture',
            ]

        if self == ExportVersion.ATOM_2_1:
            return [
                'accessionNumber',
                'acquisitionDate',
                'sourceOfAcquisition',
                'locationInformation',
                'acquisitionType',
                'resourceType',
                'title',
                'creators',
                'qubitParentSlug',
                'archivalHistory',
                'scopeAndContent',
                'appraisal',
                'physicalCondition',
                'receivedExtentUnits',
                'processingStatus',
                'processingPriority',
                'processingNotes',
                'donorName',
                'donorStreetAddress',
                'donorCity',
                'donorRegion',
                'donorCountry',
                'donorPostalCode',
                'donorTelephone',
                'donorEmail',
                'culture',
            ]

        raise ValueError(f'Unexpected ExportVersion: {repr(self)}')
