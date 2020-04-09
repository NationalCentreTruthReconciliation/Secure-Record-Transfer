from collections import OrderedDict
import logging

LOGGER = logging.getLogger(__name__)
DEFAULT_REPOSITORY = 'NCTR'

class CaaisTagger:
    @staticmethod
    def convert_form_to_tags(cleaned_form_data: dict):
        # TODO: Maybe we should catch KeyErrors here and log those
        section_1 = get_section_1_identity_information(cleaned_form_data)
        section_2 = get_section_2_source_information(cleaned_form_data)
        section_3 = get_section_3_materials_information(cleaned_form_data)
        section_4 = get_section_4_management_information(cleaned_form_data)
        section_5 = get_section_5_event_information(cleaned_form_data)
        section_6 = get_section_6_general_information(cleaned_form_data)
        section_7 = get_section_7_control_information(cleaned_form_data)

        caais_tags = OrderedDict()
        caais_tags['identityInformation'] = section_1
        caais_tags['sourceInformation'] = section_2
        caais_tags['materialsInformation'] = section_3
        caais_tags['managementInformation'] = section_4
        caais_tags['eventInformation'] = section_5
        caais_tags['generalInformation'] = section_6
        caais_tags['controlInformation'] = section_7
        return caais_tags


def get_section_1_identity_information(cleaned_form_data: dict):
    identity_info = OrderedDict()
    identity_info['repository'] = DEFAULT_REPOSITORY
    identity_info['accessionIdentifier'] = ''
    identity_info['otherIdentifiers'] = []

    if 'formset-otheridentifiers' in cleaned_form_data:
        for other_id_form in cleaned_form_data['formset-otheridentifiers']:
            if not other_id_form:
                continue
            other_identifier = OrderedDict()
            other_identifier['otherIdentifierType'] = other_id_form['other_identifier_type']
            other_identifier['otherIdentifierValue'] = other_id_form['identifier_value']
            if 'identifier_note' in other_id_form:
                other_identifier['otherIdentifierNote'] = other_id_form['identifier_note']
            identity_info['otherIdentifiers'].append(other_identifier)
    else:
        LOGGER.warn(msg=('Did not find formset-otheridentifiers in cleaned form data'))

    identity_info['accessionTitle'] = cleaned_form_data['collection_title']
    identity_info['archivalUnit'] = ''
    identity_info['acquisitionMethod'] = 'Digital Transfer'
    return identity_info

def get_section_2_source_information(cleaned_form_data: dict):
    source_info = OrderedDict()
    source_info['sourceOfMaterial'] = OrderedDict()
    source_info['sourceOfMaterial']['sourceType'] = cleaned_form_data['source_type']
    source_info['sourceOfMaterial']['sourceName'] = cleaned_form_data['source_name']
    source_info['sourceOfMaterial']['sourceContactInformation'] = OrderedDict()
    source_info['sourceOfMaterial']['sourceContactInformation']['contactName'] = cleaned_form_data['contact_name']
    source_info['sourceOfMaterial']['sourceContactInformation']['jobTitle'] = cleaned_form_data['job_title']
    source_info['sourceOfMaterial']['sourceContactInformation']['phoneNumber'] = cleaned_form_data['phone_number']
    source_info['sourceOfMaterial']['sourceContactInformation']['emailAddress'] = cleaned_form_data['email']
    source_info['sourceOfMaterial']['sourceContactInformation']['addressLine1'] = cleaned_form_data['address_line_1']
    source_info['sourceOfMaterial']['sourceContactInformation']['addressLine2'] = cleaned_form_data['address_line_2']
    source_info['sourceOfMaterial']['sourceContactInformation']['provinceOrState'] = cleaned_form_data['province_or_state']
    source_info['sourceOfMaterial']['sourceContactInformation']['postalOrZipCode'] = cleaned_form_data['postal_or_zip_code']
    source_info['sourceOfMaterial']['sourceContactInformation']['country'] = cleaned_form_data['country']
    source_info['sourceOfMaterial']['sourceRole'] = cleaned_form_data['source_role']
    source_info['sourceOfMaterial']['sourceNote'] = cleaned_form_data['source_note']
    source_info['custodialHistory'] = cleaned_form_data['custodial_history']
    return source_info

def get_section_3_materials_information(cleaned_form_data: dict):
    materials_info = OrderedDict()
    return materials_info

def get_section_4_management_information(cleaned_form_data: dict):
    management_info = OrderedDict()
    return management_info

def get_section_5_event_information(cleaned_form_data: dict):
    event_info = OrderedDict()
    return event_info

def get_section_6_general_information(cleaned_form_data: dict):
    general_info = OrderedDict()
    return general_info

def get_section_7_control_information(cleaned_form_data: dict):
    control_info = OrderedDict()
    return control_info
