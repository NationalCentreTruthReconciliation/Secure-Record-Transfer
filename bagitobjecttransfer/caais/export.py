from enum import Enum, auto


class ExportVersion(Enum):
    ''' Defines the different types and versions of CSVs that can be exported.
    '''

    CAAIS_1_0 = auto()
    ATOM_2_6 = auto()
    ATOM_2_3 = auto()
    ATOM_2_2 = auto()
    ATOM_2_1 = auto()

    def __str__(self):
        return f'{self.name}'

    @staticmethod
    def is_atom(version):
        ''' Determine if version is an AtoM version.
        '''
        return version in (
            ExportVersion.ATOM_2_1,
            ExportVersion.ATOM_2_2,
            ExportVersion.ATOM_2_3,
            ExportVersion.ATOM_2_6,
        )

    @property
    def fieldnames(self):
        ''' Get CSV column names for the specific version.
        '''

        if self == ExportVersion.CAAIS_1_0:
            # TODO: Incomplete!
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
                'sourceType',
                'sourceName',
                'sourceContactPerson',
                'sourceJobTitle',
                'sourceStreetAddress',
                'sourceCity',
                'sourceRegion',
                'sourcePostalCode',
                'sourceCountry',
                'sourcePhoneNumber',
                'sourceEmail',
                'sourceRole',
                'sourceNote',
                'sourceConfidentiality',
                'custodialHistory',
                'dateOfMaterial',
                'extentStatementType',
                'quantityAndTypeOfUnits',
                'extentStatementNote',
                'scopeAndContent',
                'languageOfMaterial',
                'storageLocation',
                'rightsStatementType',
                'rightsStatementValue',
                'rightsStatementNote',
                'materialAssessmentStatementType',
                'materialAssessmentStatementValue',
                'materialAssessmentActionPlan',
                'materialAssessmentStatementNote',
                'appraisalStatementType',
                'appraisalStatementValue',
                'appraisalStatementNote',
                # 'associatedDocumentationType',
                # 'associatedDocumentationTitle',
                # 'associatedDocumentationNote',
                'eventType',
                'eventDate',
                'eventAgent',
                'eventNote',
                'generalNote',
                'rulesOrConventions',
                'levelOfDetail',
                'actionType',
                'actionDate',
                'actionAgent',
                'actionNote',
                'languageOfAccessionRecord',
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
