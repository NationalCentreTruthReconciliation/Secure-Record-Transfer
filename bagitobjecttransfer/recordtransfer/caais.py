''' This file contains functions to assist in converting the cleaned transfer form into different
data structures. The following hierarchy shows what data can be transformed into what. You may only
go down in the hierarchy, so for example it is not possible to create the transfer form from the
flat metadata.

::

    |__ Cleaned Transfer Form
        |__ Nested CAAIS Metadata Tree
            |__ Flat CAAIS Metadata Dictionary

'''
from collections import OrderedDict

from caais.models import Metadata, Identifier, ArchivalUnit, DispositionAuthority, SourceOfMaterial, \
    PreliminaryCustodialHistory, ExtentStatement, ExtentType, PreliminaryScopeAndContent, LanguageOfMaterial, \
    StorageLocation, Rights, RightsType, PreservationRequirement, PreservationRequirementType
from recordtransfer import settings
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
    # 1.2 Identifiers
    curr_tree['identifiers'] = []
    # Accession identifier is required so we add it separately.
    curr_tree['identifiers'].append(
        OrderedDict({
            'identifier_type': 'Accession Identifier',
            'identifier_value': get_mandatory_field(
                form_data=form_data,
                caais_key='accession_identifier',
                section=curr_section),
            'identifier_note': '',
        })
    )
    formset_key = 'formset-otheridentifiers'
    if formset_key in form_data and form_data[formset_key]:
        valid_forms = [x for x in form_data[formset_key] if x]
        for other_identifier_form in valid_forms:
            other_identifier = OrderedDict()
            # 1.2.1 Identifier Type
            other_identifier['identifier_type'] = get_mandatory_field(
                form_data=other_identifier_form,
                caais_key='identifier_type',
                section=curr_section)
            # 1.2.2 Identifier Value
            other_identifier['identifier_value'] = get_mandatory_field(
                form_data=other_identifier_form,
                caais_key='identifier_value',
                section=curr_section)
            # 1.2.3 Identifier Note
            other_identifier['identifier_note'] = get_optional_field(
                form_data=other_identifier_form,
                caais_key='identifier_note',
                section=curr_section)
            curr_tree['identifiers'].append(other_identifier)
    # 1.3 Accession Title
    curr_tree['accession_title'] = get_mandatory_field(
        form_data=form_data,
        caais_key='accession_title',
        section=curr_section)
    # 1.4 Archival Unit
    curr_tree['archival_unit'] = get_mandatory_field(
        form_data=form_data,
        caais_key='archival_unit',
        section=curr_section)
    # 1.5 Acquisition Method
    curr_tree['acquisition_method'] = get_mandatory_field(
        form_data=form_data,
        caais_key='acquisition_method',
        section=curr_section)
    # 1.6 Disposition Authority - Technically Conditional, treating as Optional
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
    other_id_types = []
    other_id_values = []
    other_id_notes = []
    for other_id in section_1['identifiers']:
        other_id_types.append(other_id['identifier_type'])
        other_id_values.append(other_id['identifier_value'])
        other_id_notes.append(other_id['identifier_note'] or 'NULL')
    flat['identifierTypes'] = '|'.join(other_id_types)
    flat['identifierValues'] = '|'.join(other_id_values)
    flat['identifierNotes'] = '|'.join(other_id_notes)
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
    curr_tree['source_of_information']['source_type'] = str(get_optional_field(
        form_data=form_data,
        caais_key='source_type',
        section=curr_section))
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
    curr_tree['source_of_information'][contact_info_field]['city'] = get_mandatory_field(
        form_data=form_data,
        caais_key='city',
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
    curr_tree['source_of_information']['source_role'] = str(get_mandatory_field(
        form_data=form_data,
        caais_key='source_role',
        section=curr_section))
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
    flat['sourceContactPerson'] = contact_info['contact_name']
    flat['sourceJobTitle'] = contact_info['job_title']
    flat['sourceStreetAddress'] = ', '.join(filter(None, (
        contact_info['address_line_1'],
        contact_info['address_line_2'],
    )))
    flat['sourceCity'] = contact_info['city']
    flat['sourceRegion'] = contact_info['province_or_state']
    flat['sourcePostalCode'] = contact_info['postal_or_zip_code']
    flat['sourceCountry'] = contact_info['country']
    flat['sourcePhoneNumber'] = contact_info['phone_number']
    flat['sourceEmail'] = contact_info['email']

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
            # These are objects so the str() gets us the name as string.
            rights['rights_statement_type'] = str(get_mandatory_field(
                form_data=rights_form,
                caais_key='rights_statement_type',
                section=curr_section))
            # 4.2.2 Rights Statement Value
            rights['rights_statement_value'] = get_optional_field(
                form_data=rights_form,
                caais_key='rights_statement_value',
                section=curr_section)
            # 4.2.3 Rights Statement Note
            rights['rights_statement_note'] = get_optional_field(
                form_data=rights_form,
                caais_key='rights_statement_note',
                section=curr_section)
            rights['other_rights_statement_type'] = get_optional_field(
                form_data=rights_form,
                caais_key='other_rights_statement_type',
                section=curr_section)
            curr_tree['rights_statement'].append(rights)
    # 4.3 Preservation Requirement - Repeatable
    curr_tree['preservation_requirement'] = []
    new_assessment = OrderedDict()
    # 4.3.1 Preservation Requirement Type
    new_assessment['preservation_requirement_type'] = get_mandatory_field(
        form_data=form_data,
        caais_key='preservation_requirement_type',
        section=curr_section)
    # 4.3.2 Preservation Requirement Value
    new_assessment['preservation_requirement_value'] = get_mandatory_field(
        form_data=form_data,
        caais_key='preservation_requirement_value',
        section=curr_section)
    # 4.3.3 Preservation Requirement Note
    new_assessment['preservation_requirement_note'] = get_optional_field(
        form_data=form_data,
        caais_key='preservation_requirement_note',
        section=curr_section)
    curr_tree['preservation_requirement'].append(new_assessment)
    # Possible Contact Assessment as a second Preservation Requirment section.
    condition_assessment = get_optional_field(
        form_data=form_data,
        caais_key='condition_assessment',
        section=curr_section
    )
    if len(condition_assessment) > 0:
        physical_assessment = OrderedDict()
        physical_assessment['preservation_requirement_type'] = 'Contact assessment'
        physical_assessment['preservation_requirement_value'] = condition_assessment
        physical_assessment['preservation_requirement_note'] = ''
        curr_tree['preservation_requirement'].append(physical_assessment)

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


def _get_property_fields(form_data: dict, section_name: str) -> dict:
    property_fields = {
        'section_1': [
            'repository',
            'accession_title',
            'acquisition_method',
            'status'
        ],
        'section_2': [
            'source_type',
            'source_name',
            'source_role',
            'contact_name',
            'job_title',
            'phone_number',
            'email',
            'address_line_1',
            'address_line_2',
            'city',
            'province_or_state',
            'postal_or_zip_code',
            'country'
        ],
        'section_4': [
            'storage_location',
            'rights_statement',
            'material_assessment_statement',
            'condition_assessment'
        ]
    }
    return {f: v for f, v in form_data.items() if f in property_fields[section_name]}


def convert_form_data_to_metadata(form_data: dict) -> Metadata:
    arranged_data = convert_transfer_form_to_meta_tree(form_data)
    metadata = _convert_form_to_caais_section_1(arranged_data['section_1'])
    _convert_form_to_caais_section_2(metadata, arranged_data['section_2'])
    _convert_form_to_caais_section_3(metadata, arranged_data['section_3'])
    _convert_form_to_caais_section_4(metadata, arranged_data['section_4'])


def _convert_form_to_caais_section_1(form_data: dict) -> Metadata:
    """ Convert form data into the top-level Metadata model and any necessary
    associated models.

    Args:
        form_data (dict): The section 1 form data

    Return: The top-level metadata object.
    """
    # Make the main CAAIS object
    section_1_data = _get_property_fields(form_data, 'section_1')
    # 1.1 Repository, 1.3 Accession Title & 1.5 Acqusition Method as properties.
    metadata = Metadata(section_1_data)
    metadata.save()
    # 1.2 Create identifiers.
    for identifier in form_data['identifiers']:
        identifier['metadata'] = metadata
        new_id = Identifier(identifier)
        new_id.save()
    # 1.4 Archival Unit, if it exists.
    if form_data['archival_unit']:
        archival_unit = ArchivalUnit({
            'metadata': metadata,
            'archival_unit': form_data['archival_unit']
        })
        archival_unit.save()
    # 1.6 Disposition Authority, if it exists.
    if form_data['disposition_authority']:
        disp_auth = DispositionAuthority({
            'metadata': metadata,
            'disposition_authority': form_data['disposition_authority']
        })
        disp_auth.save()


def _convert_form_to_caais_section_2(metadata: Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 2 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 2 form data.
    """
    # The Source of Material has contact information as direct properties so move them up to the top-level.
    form_data.update(form_data['source_contact_information'])
    del(form_data['source_contact_information'])
    source_data = _get_property_fields(form_data, 'section_2')
    source_data['metadata'] = metadata
    # 2.1 Source of Material
    source = SourceOfMaterial(source_data)
    source.save()
    if form_data['custodial_history']:
        # 2.2 Preliminary Custodial History
        custodial = PreliminaryCustodialHistory({
            'metadata': metadata,
            'preliminary_custodial_history': form_data['custodial_history']
        })
        custodial.save()


def _convert_form_to_caais_section_3(metadata: Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 3 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 3 form data.
    """
    # 3.1 Date of Material (stored on the main Metadata)
    metadata.date_of_material = form_data['date_of_material']
    for extent in form_data['extent_statement']:
        # 3.2 Extent Statement
        # We generate a single Extent Statement with only the type, quantity and units and a note.
        statement = ExtentStatement({
            'metadata': metadata
        })
        # 3.2.1 Extent type, try to reuse existing entries.
        ext_type = ExtentType.objects.filter(name=extent['extent_statement_type']).first()
        if ext_type is None:
            ext_type = ExtentType()
            ext_type.name = extent['extent_statement_type']
            ext_type.save()
        statement.extent_type = ext_type
        # 3.2.2 Quantity and Unit of Measure
        statement.quantity_and_unit_of_measure = extent['quantity_and_type_of_units']
        # 3.2.6 Extent Note
        statement.extent_note = extent['extent_statement_note']
        statement.save()
    # 3.3 Preliminary Scope and Content
    scope = PreliminaryScopeAndContent({
        'metadata': metadata,
        'preliminary_scope_and_content': form_data['scope_and_content']
    })
    scope.save()
    # 3.4 Language of Material
    # Split languages on comma and standardize as lowercase in the database.
    # langs = [x.strip().lower() for x in form_data['language_of_material'].split(',')]
    # for lang in langs:
    language = LanguageOfMaterial({
        'metadata': metadata,
        'language_of_material': form_data['language_of_material']
    })
    language.save()


def _convert_form_to_caais_section_4(metadata: Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 4 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 4 form data.
    """
    # 4 Management Information Section
    # 4.1 Storage Location - Currently no entry point for location
    location = form_data['storage_location']
    storage_location = StorageLocation.objects.filter(storage_location=location).first()
    if not storage_location:
        storage_location = StorageLocation()
        storage_location.storage_location = location
        storage_location.save()
    metadata.storage_location = storage_location
    # 4.2 Rights
    for rights_statement in form_data['rights_statement']:
        right = Rights()
        right.metadata = metadata
        # 4.2.1 Rights Type
        rights_statement_type = rights_statement['rights_statement_type'] if \
            rights_statement['rights_statement_type'] == 'Other' else rights_statement['other_rights_statement_type']
        rights_type = RightsType.objects.filter(name=rights_statement_type).first()
        if not rights_type:
            rights_type = RightsType()
            rights_type.name = rights_statement_type
        right.rights_type = rights_type
        # 4.1.2 Rights Value
        right.rights_value = rights_statement['rights_statement_value']
        # 4.1.3 Rights Note
        right.rights_note = rights_statement['rights_statement_note']
        right.save()
    # 4.3 Preservation Requirements
    for preservation_requirement in form_data['preservation_requirement']:
        requirement_type = PreservationRequirementType.objects\
            .filter(name=preservation_requirement['preservation_requirement_type']).first()
        if not requirement_type:
            requirement_type = PreservationRequirementType()
            requirement_type.name = preservation_requirement['preservation_requirement_type']
        requirement = PreservationRequirement({
            'metadata': metadata,
            'requirement_type': requirement_type,
            'requirement_value': preservation_requirement['preservation_requirement_value'],
            'requirement_note': preservation_requirement['preservation_requirement_note']
        })
        requirement.save()


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
