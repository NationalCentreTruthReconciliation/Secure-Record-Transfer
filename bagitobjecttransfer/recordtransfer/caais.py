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

def _get_section_1_tree(form_data: dict):
    curr_tree = OrderedDict()
    curr_section = 'section_1'
    # 1.1 Repository
    curr_tree['repository'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='repository',
        section=curr_section,
        default_data_key='repository')
    # 1.2 Accession Identifier
    curr_tree['accession_identifier'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='accession_identifier',
        section=curr_section,
        default_data_key='accession_identifier')
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
                form_data_key='other_identifier_type',
                section=curr_section,
                default_data_key='other_identifier_type')
            # 1.3.2 Other Identifier Value
            other_identifier['other_identifier_value'] = get_mandatory_field(
                form_data=other_identifier_form,
                form_data_key='identifier_value',
                section=curr_section,
                default_data_key='other_identifier_value')
            # 1.3.3 Other Identifier Note
            other_identifier['other_identifier_note'] = get_optional_field(
                form_data=other_identifier_form,
                form_data_key='identifier_note',
                section=curr_section,
                default_data_key='other_identifier_note')
            curr_tree['other_identifier'].append(other_identifier)
    # 1.4 Accession Title
    curr_tree['accession_title'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='collection_title',
        section=curr_section,
        default_data_key='accession_title')
    # 1.5 Archival Unit
    curr_tree['archival_unit'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='archival_unit',
        section=curr_section,
        default_data_key='archival_unit')
    # 1.6 Acquisition Method
    curr_tree['acquisition_method'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='acquisition_method',
        section=curr_section,
        default_data_key='acquisition_method')
    # 1.7 Disposition Authority - Technically Conditional, treating as Optional
    curr_tree['disposition_authority'] = get_optional_field(
        form_data=form_data,
        form_data_key='disposition_authority',
        section=curr_section,
        default_data_key='disposition_authority')
    return curr_tree

def _get_section_2_tree(form_data):
    curr_tree = OrderedDict()
    curr_section = 'section_2'
    # 2.1 Source of Information
    curr_tree['source_of_information'] = OrderedDict()
    # 2.1.1 Source Type
    curr_tree['source_of_information']['source_type'] = get_optional_field(
        form_data=form_data,
        form_data_key='source_type',
        section=curr_section,
        default_data_key='source_type')
    # 2.1.2 Source Name - Mandatory
    curr_tree['source_of_information']['source_name'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='source_name',
        section=curr_section,
        default_data_key='source_name')
    # 2.1.3 Source Contact Information - Mandatory
    contact_info_field = 'source_contact_information'
    curr_tree['source_of_information'][contact_info_field] = OrderedDict()
    # The following fields up to 2.1.4 are technically NOT in the standard
    curr_tree['source_of_information'][contact_info_field]['contact_name'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='contact_name',
        section=curr_section,
        default_data_key='contact_name')
    curr_tree['source_of_information'][contact_info_field]['job_title'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='job_title',
        section=curr_section,
        default_data_key='job_title')
    curr_tree['source_of_information'][contact_info_field]['phone_number'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='phone_number',
        section=curr_section,
        default_data_key='phone_number')
    curr_tree['source_of_information'][contact_info_field]['email'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='email',
        section=curr_section,
        default_data_key='email')
    curr_tree['source_of_information'][contact_info_field]['address_line_1'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='address_line_1',
        section=curr_section,
        default_data_key='address_line_1')
    curr_tree['source_of_information'][contact_info_field]['address_line_2'] = get_optional_field(
        form_data=form_data,
        form_data_key='address_line_2',
        section=curr_section,
        default_data_key='address_line_2')
    curr_tree['source_of_information'][contact_info_field]['province_or_state'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='province_or_state',
        section=curr_section,
        default_data_key='province_or_state')
    curr_tree['source_of_information'][contact_info_field]['postal_or_zip_code'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='postal_or_zip_code',
        section=curr_section,
        default_data_key='postal_or_zip_code')
    curr_tree['source_of_information'][contact_info_field]['country'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='country',
        section=curr_section,
        default_data_key='country')
    # 2.1.4 Source Role - Mandatory
    curr_tree['source_of_information']['source_role'] = get_mandatory_field(
        form_data=form_data,
        form_data_key='source_role',
        section=curr_section,
        default_data_key='source_role')
    # 2.1.5 Source Note - Optional
    curr_tree['source_of_information']['source_note'] = get_optional_field(
        form_data=form_data,
        form_data_key='source_note',
        section=curr_section,
        default_data_key='source_note')
    # 2.2 Custodial History
    curr_tree['custodial_history'] = get_optional_field(
        form_data=form_data,
        form_data_key='custodial_history',
        section=curr_section,
        default_data_key='custodial_history')
    return curr_tree

def _get_section_3_tree(form_data):
    curr_tree = OrderedDict()
    return curr_tree

def _get_section_4_tree(form_data):
    curr_tree = OrderedDict()
    return curr_tree

def _get_section_5_tree(form_data):
    curr_tree = OrderedDict()
    return curr_tree

def _get_section_6_tree(form_data):
    curr_tree = OrderedDict()
    return curr_tree

def _get_section_7_tree(form_data):
    curr_tree = OrderedDict()
    return curr_tree

def get_mandatory_field(form_data: dict, form_data_key: str, section: str, default_data_key: str):
    try:
        return get_item_or_empty_string(form_data, form_data_key) or \
            DEFAULT_DATA[section][default_data_key]
    except KeyError as exc:
        friendly_name = default_data_key.replace('_', ' ')
        raise MetadataConversionError(
            f'Could not find a {friendly_name} for transfer. Tried "{form_data_key}" key in form, '
            f'and "{default_data_key}" in "{section}" of the DEFAULT_DATA dictionary.') from exc

def get_optional_field(form_data: dict, form_data_key: str, section: str, default_data_key: str):
    return get_item_or_empty_string(form_data, form_data_key) or \
        get_item_or_empty_string(DEFAULT_DATA, section, default_data_key)

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
