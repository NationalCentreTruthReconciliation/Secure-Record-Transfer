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
            return [
                # Section 1
                'repository',                     # 1.1 Repository
                'identifierTypes',                # 1.2.1 Identifiers => Identifier Type
                'identifierValues',               # 1.2.2 Identifiers => Identifier Value
                'identifierNotes',                # 1.2.3 Identifiers => Identifier Note
                'accessionTitle',                 # 1.3 Accession Title
                'archivalUnits',                  # 1.4 Archival Unit
                'acquisitionMethod',              # 1.5 Acquisition Method
                'dispositionAuthority',           # 1.6 Disposition Authority
                'status',                         # 1.7 Status

                # Section 2
                'sourceType',                     # 2.1.1 Source of material => Source Type
                'sourceName',                     # 2.1.2 Source of material => Source Name
                'sourceContactPerson',            # 2.1.3 Source of material => Source Contact Information
                'sourceJobTitle',                 # "
                'sourceStreetAddress',            # "
                'sourceCity',                     # "
                'sourceRegion',                   # "
                'sourcePostalCode',               # "
                'sourceCountry',                  # "
                'sourcePhoneNumber',              # "
                'sourceEmail',                    # "
                'sourceRole',                     # 2.1.4 Source of material => Source Role
                'sourceNote',                     # 2.1.5 Source of material => Source Note
                'sourceConfidentiality',          # 2.1.6 Source of material => Source Confidentiality
                'preliminaryCustodialHistories',  # 2.2 Preliminary Custodial History

                # Section 3
                'dateOfMaterials',                # 3.1 Date of Materials
                'extentStatementTypes',           # 3.2.1 Extent Statement => Extent Type
                'quantityAndUnitOfMeasure',       # 3.2.2 Extent Statement => Quantity and Unit of Measure
                'contentTypes',                   # 3.2.3 Extent Statement => Content Type
                'carrierTypes',                   # 3.2.4 Extent Statement => Carrier Type
                'extentNotes',                    # 3.2.5 Extent Statement => Extent Note
                'preliminaryScopeAndContents',    # 3.3 Preliminary Scope and Content
                'languageOfMaterials',            # 3.4 Language of Material

                # Section 4
                'storageLocation',                # 4.1 Storage Location
                'rightsStatementType',            # 4.2.1 Rights => Rights Type
                'rightsStatementValue',           # 4.2.2 Rights => Rights Value
                'rightsStatementNote',            # 4.2.3 Rights => Rights Note
                'preservationRequirementsTypes',  # 4.3.1 Preservation Requirements => Preservation Requirements Type
                'preservationRequirementsValues', # 4.3.2 Preservation Requirements => Preservation Requirements Value
                'preservarionRequirementsNotes',  # 4.3.3 Preservation Requirements => Preservation Requirements Note
                'appraisalStatementType',         # 4.4.1 Appraisal => Appraisal Types
                'appraisalStatementValue',        # 4.4.2 Appraisal => Appraisal Values
                'appraisalStatementNote',         # 4.4.3 Appraisal => Appraisal Notes
                'associatedDocumentationTypes',   # 4.5.1 Associated Documentation => Associated Documentation Type
                'associatedDocumentationTitles',  # 4.5.2 Associated Documentation => Associated Documentation Title
                'associatedDocumentationNote',    # 4.5.3 Associated Documentation => Assocaited Documentation Note

                # Section 5
                'eventTypes',                     # 5.1.1 Events => Event Type
                'eventDates',                     # 5.1.2 Events => Event Date
                'eventAgents',                    # 5.1.3 Events => Event Agent
                'eventNotes',                     # 5.1.4 Events => Event Note

                # Section 6
                'generalNotes',                   # 6.1 General Note

                # Section 7
                'rulesOrConventions',             # 7.1 Rules or Conventions
                'creationOrRevisionTypes',        # 7.2.1 Date of Creation or Revision => Creation or Revision Type
                'creationOrRevisionDates',        # 7.2.2 Date of Creation or Revision => Creation or Revision Date
                'creationOrRevisionAgents',       # 7.2.3 Date of Creation or Revision => Creation or Revision Agent
                'creationOrRevisionNotes',        # 7.2.4 Date of Creation or Revision => Creation or Revision Note
                'languageOfAccessionRecord',      # 7.3 Language of Accession Record
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
