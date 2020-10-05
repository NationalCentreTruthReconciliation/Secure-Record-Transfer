''' Tools to help convert a form from a flat data structure into a nested structure representing
the different heading levels in the CAAIS document.

If a field is mandatory and the data is in the form, the form data is used. If the form data is not
present, the default data is used. If the default data and the form data are both not present, an
exception is raised.

If a field is optional, and the data is in the form, the form data is used. If the form data is not
present, the default data is used. If the default data and the form data are both not present, the
empty string is used for the content.
'''
from collections import OrderedDict

from recordtransfer.settings import DEFAULT_DATA


class MetadataConversionError(Exception):
    pass


def convert_transfer_form_to_meta_tree(form_data: dict):
    ''' Converts the (mostly) flat form data dictionary into a tree representation of the CAAIS
    metadata.
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

def convert_meta_tree_to_bagit_tags(meta_tree: OrderedDict):
    bagit_tags = OrderedDict()
    _create_tags_recursively(meta_tree, bagit_tags)
    return dict(bagit_tags)

def _create_tags_recursively(curr_tree: OrderedDict, bagit_tags: OrderedDict):
    for key, value in curr_tree.items():
        if isinstance(value, dict):
            _create_tags_recursively(value, bagit_tags)
        elif isinstance(value, list):
            for i, entry in enumerate(value, 1):
                string_index = str(i)
                for list_item_key, list_item_value in entry.items():
                    camel_case_key = _snake_to_camel_case(list_item_key)
                    camel_case_key += string_index
                    bagit_tags[camel_case_key] = list_item_value
        else:
            camel_case_key = _snake_to_camel_case(key)
            bagit_tags[camel_case_key] = value

def _snake_to_camel_case(string: str):
    string_split = string.split('_')
    return string_split[0] + ''.join([x.capitalize() for x in string_split[1:]])

def convert_meta_tree_to_csv_row(meta_tree: OrderedDict):
    row = OrderedDict()
    row['repository'] = meta_tree['section_1']['repository']
    row['accessionIdentifier'] = meta_tree['section_1']['accession_identifier']
    other_id_types = []
    other_id_values = []
    other_id_notes = []
    for other_id in meta_tree['section_1']['other_identifier']:
        other_id_types.append(other_id['other_identifier_type'])
        other_id_values.append(other_id['other_identifier_value'])
        other_id_notes.append(other_id['other_identifier_note'] or 'NULL')
    row['otherIdentifierTypes'] = '|'.join(other_id_types)
    row['otherIdentifierValues'] = '|'.join(other_id_values)
    row['otherIdentifierNotes'] = '|'.join(other_id_notes)
    row['accessionTitle'] = meta_tree['section_1']['accession_title']
    row['archivalUnit'] = meta_tree['section_1']['archival_unit']
    row['acquisitionMethod'] = meta_tree['section_1']['acquisition_method']
    row['dispositionAuthority'] = meta_tree['section_1']['disposition_authority']
    return row

def _get_section_1_tree(form_data: dict):
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

def _get_section_2_tree(form_data):
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

def _get_section_3_tree(form_data):
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

def _get_section_4_tree(form_data):
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
    # 4.4 Appraisal Statement TODO: Not implemented
    curr_tree['appraisal_statement'] = []
    # 4.5 Associated Documentation TODO: Not implemented
    curr_tree['associated_documentation'] = []
    return curr_tree

def _get_section_5_tree(form_data):
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

def _get_section_6_tree(form_data):
    curr_tree = OrderedDict()
    curr_section = 'section_6'
    # 6.1 General Note
    curr_tree['general_note'] = get_optional_field(
        form_data=form_data,
        caais_key='general_note',
        section=curr_section)
    return curr_tree

def _get_section_7_tree(form_data):
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

def get_mandatory_field(form_data: dict, caais_key: str, section: str):
    try:
        return get_item_or_empty_string(form_data, caais_key) or \
            DEFAULT_DATA[section][caais_key]
    except KeyError as exc:
        friendly_name = caais_key.replace('_', ' ')
        raise MetadataConversionError(
            f'Could not find a {friendly_name} for transfer. Tried "{caais_key}" key in form, '
            f'and "{caais_key}" in "{section}" of the DEFAULT_DATA dictionary.') from exc

def get_optional_field(form_data: dict, caais_key: str, section: str):
    return get_item_or_empty_string(form_data, caais_key) or \
        get_item_or_empty_string(DEFAULT_DATA, section, caais_key)

def get_item_or_empty_string(dictionary, *keys):
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
