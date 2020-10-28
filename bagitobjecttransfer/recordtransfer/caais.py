''' This file contains functions to assist in converting the cleaned transfer form into different
data structures. The following hierarchy shows what data can be transformed into what. You may only
go down in the hierarchy, so for example it is not possible to create the transfer form from the
flat metadata.

.. code-block::

    |__ Cleaned Transfer Form
        |__ Nested CAAIS Metadata Tree
            |__ Flat CAAIS Metadata Dictionary

'''
from collections import OrderedDict

from recordtransfer.settings import DEFAULT_DATA


class MetadataConversionError(Exception):
    ''' Raised if an error occurs in the conversion of the metadata between different forms '''


def convert_transfer_form_to_meta_tree(form_data: dict):
    ''' Converts the cleaned transfer form data dictionary into a tree representation of the CAAIS
    metadata.

    If a field is mandatory and the data is in the form, the form data is used. If the form data is
    not present, the default data is used. If the default data and the form data are both not
    present, an exception is raised.

    If a field is optional, and the data is in the form, the form data is used. If the form data is
    not present, the default data is used. If the default data and the form data are both not
    present, the empty string is used for the content.

    Args:
        form_data (dict): The cleaned form data that a user submitted from their transfer.

    Returns:
        (OrderedDict): An ordered dictionary with an expanded structure based on the CAAIS fields.
    '''
    tree = OrderedDict()
    tree['section_1'] = _get_section_1_tree(form_data)
    tree['section_2'] = _get_section_2_tree(form_data)
    tree['section_3'] = _get_section_3_tree(form_data)
    tree['section_4'] = _get_section_4_tree(form_data)
    tree['section_5'] = _get_section_5_tree(form_data)
    tree['section_6'] = _get_section_6_tree(form_data)
    tree['section_7'] = _get_section_7_tree(form_data)
    return tree

def flatten_meta_tree(meta_tree: OrderedDict):
    ''' Converts the CAAIS metadata tree into a flat structure. Repeating fields are separated by
    pipe | characters in a single cell. This flat structure is suitable for creating a CSV row or
    BagIt tags from the metadata.

    Args:
        meta_tree (OrderedDict): The CAAIS structure created from a user's transfer form.

    Returns:
        (OrderedDict): A flat dictionary with camelCase column names.
    '''
    flattened = OrderedDict()
    _flatten_section_1_tree(meta_tree['section_1'], flattened)
    _flatten_section_2_tree(meta_tree['section_2'], flattened)
    _flatten_section_3_tree(meta_tree['section_3'], flattened)
    _flatten_section_4_tree(meta_tree['section_4'], flattened)
    _flatten_section_5_tree(meta_tree['section_5'], flattened)
    _flatten_section_6_tree(meta_tree['section_6'], flattened)
    _flatten_section_7_tree(meta_tree['section_7'], flattened)
    return flattened

def _get_section_1_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 1 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 1 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_1'
    # 1.1 Repository
    curr_tree['repository'] = get_mandatory_field(
        form_data=form_data,
        caais_key='repository',
        section=curr_section)
    # 1.2 Accession Identifier
    curr_tree['accession_identifier'] = get_mandatory_field(
        form_data=form_data,
        caais_key='accession_identifier',
        section=curr_section)
    # 1.3 Other Identifier - Optional, Repeatable
    curr_tree['other_identifier'] = []
    formset_key = 'formset-otheridentifiers'
    if formset_key in form_data and form_data[formset_key]:
        valid_forms = [x for x in form_data[formset_key] if x]
        for other_identifier_form in valid_forms:
            other_identifier = OrderedDict()
            # 1.3.1 Other Identifier Type
            other_identifier['other_identifier_type'] = get_mandatory_field(
                form_data=other_identifier_form,
                caais_key='other_identifier_type',
                section=curr_section)
            # 1.3.2 Other Identifier Value
            other_identifier['other_identifier_value'] = get_mandatory_field(
                form_data=other_identifier_form,
                caais_key='other_identifier_value',
                section=curr_section)
            # 1.3.3 Other Identifier Note
            other_identifier['other_identifier_note'] = get_optional_field(
                form_data=other_identifier_form,
                caais_key='other_identifier_note',
                section=curr_section)
            curr_tree['other_identifier'].append(other_identifier)
    # 1.4 Accession Title
    curr_tree['accession_title'] = get_mandatory_field(
        form_data=form_data,
        caais_key='accession_title',
        section=curr_section)
    # 1.5 Archival Unit
    curr_tree['archival_unit'] = get_mandatory_field(
        form_data=form_data,
        caais_key='archival_unit',
        section=curr_section)
    # 1.6 Acquisition Method
    curr_tree['acquisition_method'] = get_mandatory_field(
        form_data=form_data,
        caais_key='acquisition_method',
        section=curr_section)
    # 1.7 Disposition Authority - Technically Conditional, treating as Optional
    curr_tree['disposition_authority'] = get_optional_field(
        form_data=form_data,
        caais_key='disposition_authority',
        section=curr_section)
    return curr_tree

def _flatten_section_1_tree(section_1: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 1.

    Args:
        section_1 (OrderedDict): Section 1 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['repository'] = section_1['repository']
    flat['accessionIdentifier'] = section_1['accession_identifier']
    other_id_types = []
    other_id_values = []
    other_id_notes = []
    for other_id in section_1['other_identifier']:
        other_id_types.append(other_id['other_identifier_type'])
        other_id_values.append(other_id['other_identifier_value'])
        other_id_notes.append(other_id['other_identifier_note'] or 'NULL')
    flat['otherIdentifierTypes'] = '|'.join(other_id_types)
    flat['otherIdentifierValues'] = '|'.join(other_id_values)
    flat['otherIdentifierNotes'] = '|'.join(other_id_notes)
    flat['accessionTitle'] = section_1['accession_title']
    flat['archivalUnit'] = section_1['archival_unit']
    flat['acquisitionMethod'] = section_1['acquisition_method']
    flat['dispositionAuthority'] = section_1['disposition_authority']

def _get_section_2_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 2 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 2 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_2'
    # 2.1 Source of Information
    curr_tree['source_of_information'] = OrderedDict()
    # 2.1.1 Source Type
    curr_tree['source_of_information']['source_type'] = get_optional_field(
        form_data=form_data,
        caais_key='source_type',
        section=curr_section)
    # 2.1.2 Source Name - Mandatory
    curr_tree['source_of_information']['source_name'] = get_mandatory_field(
        form_data=form_data,
        caais_key='source_name',
        section=curr_section)
    # 2.1.3 Source Contact Information - Mandatory
    contact_info_field = 'source_contact_information'
    curr_tree['source_of_information'][contact_info_field] = OrderedDict()
    # The following fields up to 2.1.4 are technically not in the standard
    curr_tree['source_of_information'][contact_info_field]['contact_name'] = get_mandatory_field(
        form_data=form_data,
        caais_key='contact_name',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['job_title'] = get_mandatory_field(
        form_data=form_data,
        caais_key='job_title',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['phone_number'] = get_mandatory_field(
        form_data=form_data,
        caais_key='phone_number',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['email'] = get_mandatory_field(
        form_data=form_data,
        caais_key='email',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['address_line_1'] = get_mandatory_field(
        form_data=form_data,
        caais_key='address_line_1',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['address_line_2'] = get_optional_field(
        form_data=form_data,
        caais_key='address_line_2',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['province_or_state'] = get_mandatory_field(
        form_data=form_data,
        caais_key='province_or_state',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['postal_or_zip_code'] = get_mandatory_field(
        form_data=form_data,
        caais_key='postal_or_zip_code',
        section=curr_section)
    curr_tree['source_of_information'][contact_info_field]['country'] = get_mandatory_field(
        form_data=form_data,
        caais_key='country',
        section=curr_section)
    # 2.1.4 Source Role - Mandatory
    curr_tree['source_of_information']['source_role'] = get_mandatory_field(
        form_data=form_data,
        caais_key='source_role',
        section=curr_section)
    # 2.1.5 Source Note - Optional
    curr_tree['source_of_information']['source_note'] = get_optional_field(
        form_data=form_data,
        caais_key='source_note',
        section=curr_section)
    # 2.2 Custodial History
    curr_tree['custodial_history'] = get_optional_field(
        form_data=form_data,
        caais_key='custodial_history',
        section=curr_section)
    return curr_tree

def _flatten_section_2_tree(section_2: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 2.

    Args:
        section_2 (OrderedDict): Section 2 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['sourceType'] = section_2['source_of_information']['source_type']
    flat['sourceName'] = section_2['source_of_information']['source_name']

    contact_info = section_2['source_of_information']['source_contact_information']
    contact_address = (
        '{line1and2}, {province}  {postal} ({country})'
    ).format(
        line1and2=contact_info['address_line_1'] if not contact_info['address_line_2'] else \
            f"{contact_info['address_line_1']} {contact_info['address_line_2']}",
        province=contact_info['province_or_state'],
        postal=contact_info['postal_or_zip_code'],
        country=contact_info['country'],
    )

    flat['sourceContactInformation'] = (
        'NAME: {name}|JOB: {job}|PHONE: {phone}|EMAIL: {email}|ADDRESS: {address}'
    ).format(
        name=contact_info['contact_name'],
        job=contact_info['job_title'],
        phone=contact_info['phone_number'],
        email=contact_info['email'],
        address=contact_address,
    )

    flat['sourceRole'] = section_2['source_of_information']['source_role']
    flat['sourceNote'] = section_2['source_of_information']['source_note']
    flat['custodialHistory'] = section_2['custodial_history']

def _get_section_3_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 3 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 3 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_3'
    # 3.1 Date of Material
    curr_tree['date_of_material'] = get_mandatory_field(
        form_data=form_data,
        caais_key='date_of_material',
        section= curr_section)
    # 3.2 Extent Statement - Technically repeatable, but we only include one array item
    curr_tree['extent_statement'] = []
    new_extent = OrderedDict()
    # 3.2.1 Extent Statement Type
    new_extent['extent_statement_type'] = get_mandatory_field(
        form_data=form_data,
        caais_key='extent_statement_type',
        section=curr_section)
    # 3.2.2 Quantity and Type of Units
    new_extent['quantity_and_type_of_units'] = get_mandatory_field(
        form_data=form_data,
        caais_key='quantity_and_type_of_units',
        section=curr_section)
    # 3.2.3 Extent Statement Note
    new_extent['extent_statement_note'] = get_optional_field(
        form_data=form_data,
        caais_key='extent_statement_note',
        section=curr_section)
    curr_tree['extent_statement'].append(new_extent)
    # 3.3 Scope and Content
    curr_tree['scope_and_content'] = get_mandatory_field(
        form_data=form_data,
        caais_key='scope_and_content',
        section=curr_section)
    # 3.4 Language of Material
    curr_tree['language_of_material'] = get_mandatory_field(
        form_data=form_data,
        caais_key='language_of_material',
        section=curr_section)
    return curr_tree

def _flatten_section_3_tree(section_3: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 3.

    Args:
        section_3 (OrderedDict): Section 3 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['dateOfMaterial'] = section_3['date_of_material']
    extent_types = []
    quantity_and_type_of_units = []
    extent_note = []
    for extent in section_3['extent_statement']:
        extent_types.append(extent['extent_statement_type'])
        quantity_and_type_of_units.append(extent['quantity_and_type_of_units'])
        extent_note.append(extent['extent_statement_note'] or 'NULL')
    flat['extentStatementType'] = '|'.join(extent_types)
    flat['quantityAndTypeOfUnits'] = '|'.join(quantity_and_type_of_units)
    flat['extentStatementNote'] = '|'.join(extent_note)
    flat['scopeAndContent'] = section_3['scope_and_content']
    flat['languageOfMaterial'] = section_3['language_of_material']

def _get_section_4_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 4 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 4 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_4'
    # 4.1 Storage Location
    curr_tree['storage_location'] = get_mandatory_field(
        form_data=form_data,
        caais_key='storage_location',
        section=curr_section)
    # 4.2 Rights Statement - Repeatable
    curr_tree['rights_statement'] = []
    formset_key = 'formset-rights'
    if formset_key in form_data and form_data[formset_key]:
        valid_forms = [x for x in form_data[formset_key] if x]
        for rights_form in valid_forms:
            rights = OrderedDict()
            # 4.2.1 Rights Statement Type
            rights['rights_statement_type'] = get_mandatory_field(
                form_data=rights_form,
                caais_key='rights_statement_type',
                section=curr_section)
            # 4.2.2 Rights Statement Value
            rights['rights_statement_value'] = get_mandatory_field(
                form_data=rights_form,
                caais_key='rights_statement_value',
                section=curr_section)
            # 4.2.3 Rights Statement Note
            rights['rights_statement_note'] = get_optional_field(
                form_data=rights_form,
                caais_key='rights_statement_note',
                section=curr_section)
            curr_tree['rights_statement'].append(rights)
    # 4.3 Material Assessment Statement - Technically repeatable, but we only include one array item
    curr_tree['material_assessment_statement'] = []
    new_assessment = OrderedDict()
    # 4.3.1 Material Assessment Statement Type
    new_assessment['material_assessment_statement_type'] = get_mandatory_field(
        form_data=form_data,
        caais_key='material_assessment_statement_type',
        section=curr_section)
    # 4.3.2 Material Assessment Statement Value
    new_assessment['material_assessment_statement_value'] = get_mandatory_field(
        form_data=form_data,
        caais_key='material_assessment_statement_value',
        section=curr_section)
    # 4.3.3 Material Assessment Action Plan
    new_assessment['material_assessment_action_plan'] = get_optional_field(
        form_data=form_data,
        caais_key='material_assessment_action_plan',
        section=curr_section)
    # 4.3.4 Material Assessment Statement Note
    new_assessment['material_assessment_statement_note'] = get_optional_field(
        form_data=form_data,
        caais_key='material_assessment_statement_note',
        section=curr_section)
    curr_tree['material_assessment_statement'].append(new_assessment)
    # 4.4 Appraisal Statement
    curr_tree['appraisal_statement'] = []
    # 4.5 Associated Documentation
    curr_tree['associated_documentation'] = []
    return curr_tree

def _flatten_section_4_tree(section_4: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 4.

    Args:
        section_4 (OrderedDict): Section 4 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['storageLocation'] = section_4['storage_location']
    rights_types = []
    rights_values = []
    rights_notes = []
    for rights in section_4['rights_statement']:
        rights_types.append(rights['rights_statement_type'])
        rights_values.append(rights['rights_statement_value'])
        rights_notes.append(rights['rights_statement_note'] or 'NULL')
    flat['rightsStatementType'] = '|'.join(rights_types)
    flat['rightsStatementValue'] = '|'.join(rights_values)
    flat['rightsStatementNote'] = '|'.join(rights_notes)
    material_types = []
    material_values = []
    action_plans = []
    material_notes = []
    for statement in section_4['material_assessment_statement']:
        material_types.append(statement['material_assessment_statement_type'])
        material_values.append(statement['material_assessment_statement_value'])
        action_plans.append(statement['material_assessment_action_plan'] or 'NULL')
        material_notes.append(statement['material_assessment_statement_note'] or 'NULL')
    flat['materialAssessmentStatementType'] = '|'.join(material_types)
    flat['materialAssessmentStatementValue'] = '|'.join(material_values)
    flat['materialAssessmentActionPlan'] = '|'.join(action_plans)
    flat['materialAssessmentStatementNote'] = '|'.join(material_notes)
    appraisal_types = []
    appraisal_values = []
    appraisal_notes = []
    for appraisal in section_4['appraisal_statement']:
        appraisal_types.append(appraisal['appraisal_statement_type'])
        appraisal_values.append(appraisal['appraisal_statement_value'])
        appraisal_notes.append(appraisal['appraisal_statement_note'] or 'NULL')
    flat['appraisalStatementType'] = '|'.join(appraisal_types)
    flat['appraisalStatementValue'] = '|'.join(appraisal_values)
    flat['appraisalStatementNote'] = '|'.join(appraisal_notes)
    doc_types = []
    doc_titles = []
    doc_notes = []
    for document in section_4['associated_documentation']:
        doc_types.append(document['associated_documentation_type'])
        doc_titles.append(document['associated_documentation_title'])
        doc_notes.append(document['associated_documentation_note'] or 'NULL')
    flat['associatedDocumentationType'] = '|'.join(doc_types)
    flat['associatedDocumentationTitle'] = '|'.join(doc_titles)
    flat['associatedDocumentationNote'] = '|'.join(doc_notes)

def _get_section_5_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 5 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 5 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_5'
    # 5.1 Event Statement - Technically repeatable, but we only include one array item
    curr_tree['event_statement'] = []
    new_event = OrderedDict()
    # 5.1.1 Event Type
    new_event['event_type'] = get_mandatory_field(
        form_data=form_data,
        caais_key='event_type',
        section=curr_section)
    # 5.1.2 Event Date
    new_event['event_date'] = get_mandatory_field(
        form_data=form_data,
        caais_key='event_date',
        section=curr_section)
    # 5.1.3 Event Agent
    new_event['event_agent'] = get_mandatory_field(
        form_data=form_data,
        caais_key='event_agent',
        section=curr_section)
    # 5.1.4 Event Note
    new_event['event_note'] = get_optional_field(
        form_data=form_data,
        caais_key='event_note',
        section=curr_section)
    curr_tree['event_statement'].append(new_event)
    return curr_tree

def _flatten_section_5_tree(section_5: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 5.

    Args:
        section_5 (OrderedDict): Section 5 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    event_types = []
    event_dates = []
    event_agents = []
    event_notes = []
    for event in section_5['event_statement']:
        event_types.append(event['event_type'])
        event_dates.append(event['event_date'])
        event_agents.append(event['event_agent'])
        event_notes.append(event['event_note'] or 'NULL')
    flat['eventType'] = '|'.join(event_types)
    flat['eventDate'] = '|'.join(event_dates)
    flat['eventAgent'] = '|'.join(event_agents)
    flat['eventNote'] = '|'.join(event_notes)

def _get_section_6_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 6 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 6 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_6'
    # 6.1 General Note
    curr_tree['general_note'] = get_optional_field(
        form_data=form_data,
        caais_key='general_note',
        section=curr_section)
    return curr_tree

def _flatten_section_6_tree(section_6: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 6.

    Args:
        section_6 (OrderedDict): Section 6 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['generalNote'] = section_6['general_note']

def _get_section_7_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 7 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 7 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_7'
    # 7.1 Rules or Conventions
    curr_tree['rules_or_conventions'] = get_optional_field(
        form_data=form_data,
        caais_key='rules_or_conventions',
        section=curr_section)
    # 7.2 Level of Detail
    curr_tree['level_of_detail'] = get_optional_field(
        form_data=form_data,
        caais_key='level_of_detail',
        section=curr_section)
    # 7.3 Date of Creation or Revision - Technically repeatable, but we only include one array item
    curr_tree['date_of_creation_or_revision'] = []
    new_date = OrderedDict()
    # 7.3.1 Action Type
    new_date['action_type'] = get_mandatory_field(
        form_data=form_data,
        caais_key='action_type',
        section=curr_section)
    # 7.3.2 Action Date
    new_date['action_date'] = get_mandatory_field(
        form_data=form_data,
        caais_key='action_date',
        section=curr_section)
    # 7.3.3 Action Agent
    new_date['action_agent'] = get_mandatory_field(
        form_data=form_data,
        caais_key='action_agent',
        section=curr_section)
    # 7.3.4 Action Note
    new_date['action_note'] = get_optional_field(
        form_data=form_data,
        caais_key='action_note',
        section=curr_section)
    curr_tree['date_of_creation_or_revision'].append(new_date)
    # 7.4 Language of Accession Record
    curr_tree['language_of_accession_record'] = get_optional_field(
        form_data=form_data,
        caais_key='language_of_accession_record',
        section=curr_section)
    return curr_tree

def _flatten_section_7_tree(section_7: OrderedDict, flat: OrderedDict):
    ''' The flat dictionary is updated with the flattened section 7.

    Args:
        section_7 (OrderedDict): Section 7 of the metadata tree
        flat (OrderedDict): The current working flat dictionary
    '''
    flat['rulesOrConventions'] = section_7['rules_or_conventions']
    flat['levelOfDetail'] = section_7['level_of_detail']
    action_types = []
    action_dates = []
    action_agents = []
    action_notes = []
    for action in section_7['date_of_creation_or_revision']:
        action_types.append(action['action_type'])
        action_dates.append(action['action_date'])
        action_agents.append(action['action_agent'])
        action_notes.append(action['action_note'] or 'NULL')
    flat['actionType'] = '|'.join(action_types)
    flat['actionDate'] = '|'.join(action_dates)
    flat['actionAgent'] = '|'.join(action_agents)
    flat['actionNote'] = '|'.join(action_notes)
    flat['languageOfAccessionRecord'] = section_7['language_of_accession_record']

def get_mandatory_field(form_data: dict, caais_key: str, section: str) -> str:
    try:
        return _get_item_or_empty_string(form_data, caais_key) or \
            DEFAULT_DATA[section][caais_key]
    except KeyError as exc:
        friendly_name = caais_key.replace('_', ' ')
        raise MetadataConversionError(
            f'Could not find a {friendly_name} for transfer. Tried "{caais_key}" key in form, '
            f'and "{caais_key}" in "{section}" of the DEFAULT_DATA dictionary.') from exc

def get_optional_field(form_data: dict, caais_key: str, section: str) -> str:
    return _get_item_or_empty_string(form_data, caais_key) or \
        _get_item_or_empty_string(DEFAULT_DATA, section, caais_key)

def _get_item_or_empty_string(dictionary: dict, *keys) -> str:
    try:
        if len(keys) == 0:
            return ''
        if len(keys) == 1:
            return dictionary[keys[0]]
        curr_value = dictionary[keys[0]]
        for key in keys[1:]:
            curr_value = curr_value[key]
        return curr_value
    except (KeyError, TypeError):
        return ''
