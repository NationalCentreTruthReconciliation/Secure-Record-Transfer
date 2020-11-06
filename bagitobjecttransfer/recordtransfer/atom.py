''' This file contains functions to assist in converting the CAAIS metadata tree into a flat
structure with the column names for an AtoM accession CSV.
'''
import re
from collections import OrderedDict
from datetime import datetime

from recordtransfer.settings import APPROXIMATE_DATE_FORMAT

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
    # 1.1 Repository -> (NO EQUIVALENT)

    # 1.2 Accession Identifier -> accessionNumber
    atom_row['accessionNumber'] = section_1['accession_identifier']

    # 1.3.1 Other Identifier Type -> alternativeIdentifierTypes
    # 1.3.1 Other Identifier Value -> alternativeIdentifiers
    # 1.3.1 Other Identifier Note -> alternativeIdentifierNotes
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

    # 1.5 Archival Unit -> (NO EQUIVALENT)

    # 1.6 Acquisition Method -> acquisitionType
    atom_row['acquisitionType'] = section_1['acquisition_method']

    # 1.7 Disposition Authority -> (NO EQUIVALENT)

def _map_section_2(section_2: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 2 of the CAAIS metadata to the atom CSV row

    Args:
        section_2 (OrderedDict): Section 2 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    source_of_info = section_2['source_of_information']
    contact_info = source_of_info['source_contact_information']

    # 2.1.1 Source Type -> donorNote (v2.6, NOT IDEAL)
    # 2.1.4 Source Role -> donorNote (v2.6, NOT IDEAL)
    # 2.1.5 Source Note -> donorNote (v2.6, NOT IDEAL)
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

    # Contact Name -> donorContactPerson (v2.6)
    # Job Title -> donorContactPerson (v2.6, NOT IDEAL)
    if version >= (2, 6):
        contact_person = f'{contact_info["contact_name"]} ({contact_info["job_title"]})'
        atom_row['donorContactPerson'] = contact_person

    # Address Line 1 -> donorStreetAddress
    # Address Line 2 -> donorStreetAddress
    # City -> donorCity
    # Province or State -> donorRegion
    # Postal or Zip Code -> donorPostalCode
    # Country -> donorCountry
    # Phone Number -> donorTelephone
    # Email -> donorEmail
    street_address = contact_info['address_line_1']
    if contact_info['address_line_2']:
        street_address += f', {contact_info["address_line_2"]}'
    atom_row['donorStreetAddress'] = street_address
    atom_row['donorCity'] = contact_info['city']
    atom_row['donorRegion'] = contact_info['province_or_state']
    atom_row['donorPostalCode'] = contact_info['postal_or_zip_code']
    atom_row['donorCountry'] = contact_info['country']
    atom_row['donorTelephone'] = contact_info['phone_number']
    atom_row['donorEmail'] = contact_info['email']

    # 2.2 Custodial History -> archivalHistory
    atom_row['archivalHistory'] = section_2['custodial_history']

def _map_section_3(section_3: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 3 of the CAAIS metadata to the atom CSV row

    Args:
        section_3 (OrderedDict): Section 3 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    date_split = section_3['date_of_material'].split(' - ')
    if len(date_split) == 1:
        date_split.append(date_split[0])

    # Used to pull the date from the approximate form
    approx_header, approx_trailer = APPROXIMATE_DATE_FORMAT.split('{date}')
    approximate_date = re.compile(
        r'^' + re.escape(approx_header) + r'(?P<date>[\d\-]+)' + re.escape(approx_trailer) + r'$'
    )
    match_obj_start = approximate_date.match(date_split[0])
    match_obj_end = approximate_date.match(date_split[1])

    # Remove the start and end of the approximate date form, if the date is approximate
    start_date = match_obj_start.group('date') if match_obj_start else date_split[0]
    end_date = match_obj_end.group('date') if match_obj_end else date_split[1]

    # 3.1 Date of Material -> creationDates, creationDatesStart, creationDatesEnd (v2.2)
    # 3.1 Date of Material -> eventDates, eventStartDates, eventEndDates (v2.3+)
    if version == (2, 2):
        atom_row['creationDates'] = section_3['date_of_material']
        atom_row['creationDatesStart'] = start_date
        atom_row['creationDatesEnd'] = end_date
        atom_row['creators'] = 'NULL'
        atom_row['creationDatesType'] = 'Creation'
    elif version >= (2, 3):
        atom_row['eventDates'] = section_3['date_of_material']
        atom_row['eventStartDates'] = start_date
        atom_row['eventEndDates'] = end_date
        atom_row['creators'] = 'NULL'
        atom_row['eventTypes'] = 'Creation'

    # 3.2.1 Extent Statement Type -> (NO EQUIVALENT)
    # 3.2.2 Quantity and Type of Units -> receivedExtentUnits
    # 3.2.3 Extent Statement Note -> (NO EQUIVALENT)
    quantities = []
    for extent in section_3['extent_statement']:
        quantities.append(extent['quantity_and_type_of_units'])
    atom_row['receivedExtentUnits'] = '|'.join(quantities)

    # 3.3 Scope and Content -> scopeAndContent
    # 3.4 Language of Material -> scopeAndContent (NOT IDEAL)
    scope = section_3['scope_and_content'].rstrip('. ')
    language = section_3['language_of_material'].rstrip('. ')
    scope_narrative = [
        scope,
        f'Language of material: {language}.'
    ]
    atom_row['scopeAndContent'] = '. '.join(scope_narrative)

def _map_section_4(section_4: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 4 of the CAAIS metadata to the atom CSV row

    Args:
        section_4 (OrderedDict): Section 4 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 4.1 Storage Location -> locationInformation
    atom_row['locationInformation'] = section_4['storage_location']

    # 4.2.1 Rights Statement Type -> (NO EQUIVALENT)
    # 4.2.2 Rights Statement Value -> (NO EQUIVALENT)
    # 4.2.3 Rights Statement Note -> (NO EQUIVALENT)

    # 4.3.1 Material Assessment Statement Type -> physicalCondition (NOT IDEAL)
    # 4.3.2 Material Assessment Statement Value -> physicalCondition
    # 4.3.3 Material Assessment Action Plan -> processingStatus
    # 4.3.4 Material Assessment Statement Note -> processingNotes
    statement_types = []
    statement_values = []
    action_plans = []
    statement_notes = []
    for statement in section_4['material_assessment_statement']:
        statement_types.append(statement['material_assessment_statement_type'])
        statement_values.append(statement['material_assessment_statement_value'])
        action_plans.append(statement['material_assessment_action_plan'] or 'NULL')
        statement_notes.append(statement['material_assessment_statement_note'] or 'NULL')
    atom_row['physicalCondition'] = '|'.join([f'Assessment Type: {x}; Statement: {y}' for \
        x, y in zip(statement_types, statement_values)
    ])
    atom_row['processingStatus'] = '|'.join(action_plans)
    atom_row['processingNotes'] = '|'.join(statement_notes)

    # 4.4.1 Appraisal Statement Type -> appraisal (NOT IDEAL)
    # 4.4.2 Appraisal Statement Value -> appraisal (NOT IDEAL)
    # 4.4.3 Appraisal Statement Note -> appraisal (NOT IDEAL)
    appraisal_types = []
    appraisal_values = []
    appraisal_notes = []
    for appraisal in section_4['appraisal_statement']:
        appraisal_types.append(appraisal['appraisal_statement_type'])
        appraisal_values.append(appraisal['appraisal_statement_value'])
        appraisal_notes.append(appraisal['appraisal_statement_note'] or 'NULL')
    atom_row['appraisal'] = '|'.join([
        f'Appraisal Type: {x}; Statement: {y}; Notes: {z}' if z != 'NULL' else \
        f'Appraisal Type: {x}; Statement: {y}' for \
        x, y, z in zip(appraisal_types, appraisal_values, appraisal_notes)
    ])

    # 4.5.1 Associated Documentation Type -> (NO EQUIVALENT)
    # 4.5.2 Associated Documentation Title -> (NO EQUIVALENT)
    # 4.5.3 Associated Documentation Note -> (NO EQUIVALENT)

def _map_section_5(section_5: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 5 of the CAAIS metadata to the atom CSV row

    Args:
        section_5 (OrderedDict): Section 5 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 5.1.1 Event Type -> (NO EQUIVALENT)
    # 5.1.2 Event Date -> (NO EQUIVALENT)
    # 5.1.3 Event Agent -> (NO EQUIVALENT)
    # 5.1.4 Event Note -> (NO EQUIVALENT)

def _map_section_6(section_6: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 6 of the CAAIS metadata to the atom CSV row

    Args:
        section_6 (OrderedDict): Section 6 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 6.1 General Note -> (NO EQUIVALENT)

def _map_section_7(section_7: OrderedDict, atom_row: OrderedDict, version: tuple):
    ''' Map section 7 of the CAAIS metadata to the atom CSV row

    Args:
        section_7 (OrderedDict): Section 7 of the CAAIS metadata structure
        atom_row (OrderedDict): The current working CSV row being mapped to
        version (tuple): The version of the AtoM CSV being generated
    '''
    # 7.1 Rules or Conventions -> (NO EQUIVALENT)
    # 7.2 Level of Detail -> (NO EQUIVALENT)

    event_types = []
    event_agents = []
    event_dates = []
    for action in section_7['date_of_creation_or_revision']:
        event_agents.append(action['action_agent'])
        if version > (2, 1):
            event_types.append(action['action_type'])
            parsed_date = datetime.strptime(action['action_date'], r'%Y-%m-%d %H:%M:%S %Z')
            yyyy_mm_dd = parsed_date.strftime(r'%Y-%m-%d')
            event_dates.append(yyyy_mm_dd)

    # 7.3.1 Action Type -> eventTypes (v2.3+)
    # 7.3.2 Action Date -> eventDates, eventStartDates, eventEndDates (v2.3+)
    # 7.3.3 Action Agent -> creators (v2.3+, NOT IDEAL)
    # 7.3.4 Action Note -> (v2.3+, NO EQUIVALENT)
    if version >= (2, 3):
        array_column_updates = [
            ('creators', event_agents),
            ('eventTypes', event_types),
            ('eventDates', event_dates),
            ('eventStartDates', event_dates),
            ('eventEndDates', event_dates),
        ]

    # 7.3.1 Action Type -> creationDatesType (v2.2, NOT IDEAL)
    # 7.3.2 Action Date -> creationDates, creationDatesStart, creationDatesEnd (v2.2, NOT IDEAL)
    # 7.3.3 Action Agent -> creators (v2.2, NOT IDEAL)
    # 7.3.4 Action Note -> (v2.2, NO EQUIVALENT)
    if version == (2, 2):
        array_column_updates = [
            ('creators', event_agents),
            ('creationDatesType', event_types),
            ('creationDates', event_dates),
            ('creationDatesStart', event_dates),
            ('creationDatesEnd', event_dates),
        ]

    # 7.3.1 Action Type -> (v2.1, NO EQUIVALENT)
    # 7.3.2 Action Date -> (v2.1, NO EQUIVALENT)
    # 7.3.3 Action Agent -> creators (v2.1, NOT IDEAL)
    # 7.3.4 Action Note -> (v2.1, NO EQUIVALENT)
    if version == (2, 1):
        array_column_updates = [
            ('creators', event_agents),
        ]

    for col_name, new_elements in array_column_updates:
        curr_elements = atom_row[col_name].split('|')
        curr_elements.extend(new_elements)
        atom_row[col_name] = '|'.join(curr_elements)

    # 7.4 Language of Accession Record -> culture (v2.x, NOT IDEAL)
    atom_row['culture'] = section_7['language_of_accession_record']

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
