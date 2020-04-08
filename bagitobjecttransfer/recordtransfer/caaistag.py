from collections import OrderedDict
import logging

LOGGER = logging.getLogger(__name__)
DEFAULT_REPOSITORY = 'NCTR'

class CaaisTagger:
    @staticmethod
    def convert_form_to_tags(cleaned_form_data: dict):
        # TODO: Maybe we should catch KeyErrors here and log those
        section_1 = get_section_1_identity_information(cleaned_form_data, caais_tags)
        section_2 = get_section_2_source_information()
        section_3 = {}
        section_4 = {}
        section_5 = {}
        section_6 = {}
        section_7 = {}

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
            other_identifier = OrderedDict()
            other_identifier['otherIdentifierType'] = other_id_form['other_identifer_type']
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
    return {}
