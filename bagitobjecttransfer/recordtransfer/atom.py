''' This file contains functions to assist in converting the CAAIS metadata tree into a flat
structure with the column names for an AtoM accession CSV.
'''
from collections import OrderedDict

accepted_versions = {
    (2, 6): [
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
    ],
    (2, 3): [
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
    ],
    (2, 2): [
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
    ],
    (2, 1): [
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
    ],
}

def flatten_meta_tree_atom_style(meta_tree: OrderedDict, version: tuple = (2, 6)):
    _check_version(version)
    atom_row = _get_empty_row(version)
    _map_section_1(meta_tree['section_1'], atom_row, version)
    _map_section_2(meta_tree['section_2'], atom_row, version)
    _map_section_3(meta_tree['section_3'], atom_row, version)
    _map_section_4(meta_tree['section_4'], atom_row, version)
    _map_section_5(meta_tree['section_5'], atom_row, version)
    _map_section_6(meta_tree['section_6'], atom_row, version)
    _map_section_7(meta_tree['section_7'], atom_row, version)
    return atom_row

def _map_section_1(section_1: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 1 of the CAAIS metadata to the atom CSV row

    Args:
        section_1 (OrderedDict): Section 1 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 1.1 Repository --- MISSING

    # 1.2 Accession Identifier -> accessionNumber
    atom_row['accessionNumber'] = section_1['accession_identifier']

    # 1.3 Other Identifier -> alternativeIdentifiers
    if version >= (2, 6):
        other_id_types = []
        other_id_values = []
        other_id_notes = []
        for other_id in section_1['other_identifier']:
            other_id_types.append(other_id['other_identifier_type'])
            other_id_values.append(other_id['other_identifier_value'])
            other_id_notes.append(other_id['other_identifier_note'] or 'NULL')
        atom_row['alternativeIdentifiers'] = '|'.join(other_id_values)
        atom_row['alternativeIdentifierTypes'] = '|'.join(other_id_types)
        atom_row['alternativeIdentifierNotes'] = '|'.join(other_id_notes)

    # 1.4 Accession Title -> title
    atom_row['title'] = section_1['accession_title']

    # 1.5 Archival Unit --- MISSING

    # 1.6 Acquisition Method -> acquisitionType
    atom_row['acquisitionType'] = section_1['acquisition_method']

    # 1.7 Disposition Authority --- MISSING

def _map_section_2(section_2: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 2 of the CAAIS metadata to the atom CSV row

    Args:
        section_2 (OrderedDict): Section 2 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    source_of_info = section_2['source_of_information']
    contact_info = source_of_info['source_contact_information']

    # 2.1.1 Source Type -> donorNote (NOT IDEAL)
    # 2.1.4 Source Role -> donorNote (NOT IDEAL)
    # 2.1.5 Source Note -> donorNote (NOT IDEAL)
    if version >= (2, 6):
        donor_narrative = [
            f'The donor is a {source_of_info["source_type"]}',
            f'Their relationship to the records is: {source_of_info["source_role"]}',
        ]
        note = source_of_info['source_note'].rstrip(r'. ')
        if note:
            donor_narrative.append(note)
        atom_row['donorNote'] = '. '.join(donor_narrative)

    # 2.1.2 Source Name -> donorName
    atom_row['donorName'] = source_of_info['source_name']

    # Contact Name -> donorContactPerson
    # Job Title -> donorContactPerson (NOT IDEAL)
    if version >= (2, 6):
        contact_person = f'{contact_info["contact_name"]} ({contact_info["job_title"]})'
        atom_row['donorContactPerson'] = contact_person

    # Phone Number -> donorTelephone
    atom_row['donorTelephone'] = contact_info['phone_number']

    # Email -> donorEmail
    atom_row['donorEmail'] = contact_info['email']

    # Address Line 1 -> donorStreetAddress
    # Address Line 2 -> donorStreetAddress
    # City -> donorCity
    # Province or State -> donorRegion
    # Postal or Zip Code -> donorPostalCode
    # Country -> donorCountry
    street_address = contact_info['address_line_1']
    if contact_info['address_line_2']:
        street_address += f', {contact_info["address_line_2"]}'
    atom_row['donorStreetAddress'] = street_address
    atom_row['donorCity'] = contact_info['city']
    atom_row['donorRegion'] = contact_info['province_or_state']
    atom_row['donorPostalCode'] = contact_info['postal_or_zip_code']
    atom_row['donorCountry'] = contact_info['country']

    # 2.2 Custodial History -> archivalHistory
    atom_row['archivalHistory'] = section_2['custodial_history']

def _map_section_3(section_3: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 3 of the CAAIS metadata to the atom CSV row

    Args:
        section_3 (OrderedDict): Section 3 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    pass

def _map_section_4(section_4: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 4 of the CAAIS metadata to the atom CSV row

    Args:
        section_4 (OrderedDict): Section 4 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    pass

def _map_section_5(section_5: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 5 of the CAAIS metadata to the atom CSV row

    Args:
        section_5 (OrderedDict): Section 5 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    pass

def _map_section_6(section_6: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 6 of the CAAIS metadata to the atom CSV row

    Args:
        section_6 (OrderedDict): Section 6 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 6.1 General Note --- MISSING

def _map_section_7(section_7: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 7 of the CAAIS metadata to the atom CSV row

    Args:
        section_7 (OrderedDict): Section 7 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    pass

def _check_version(version: tuple):
    if not isinstance(version, tuple):
        msg = f'The version parameter expected a tuple but got "{type(version)}"'
        raise ValueError(msg)
    if not len(version) == 2:
        msg = 'The version tuple must have two elements for the major and minor version'
        raise ValueError(msg)
    if version not in accepted_versions:
        msg = ('This application does not support creating AtoM Accession CSVs for version '
               f'{version[0]}.{version[1]}')

def _get_empty_row(version: tuple):
    row = OrderedDict()
    for key_name in accepted_versions[version]:
        row[key_name] = ''
    return row
