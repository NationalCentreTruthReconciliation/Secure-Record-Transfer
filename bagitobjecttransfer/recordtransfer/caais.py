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

import caais.models as c_models
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
    curr_tree['identifiers'] = []
    curr_tree['identifiers'].append(OrderedDict({
        'identifier_type': 'Accession Identifier',
        'identifier_value': get_mandatory_field(
            form_data=form_data,
            caais_key='accession_identifier',
            section=curr_section),
        'identifier_note': '',
    }))
    # 1.3 Other Identifiers
    formset_key = 'formset-otheridentifiers'
    if formset_key in form_data and form_data[formset_key]:
        valid_forms = [x for x in form_data[formset_key] if x]
        for other_identifier_form in valid_forms:
            other_identifier = OrderedDict()
            # 1.2.1 Identifier Type
            other_identifier['identifier_type'] = get_optional_field(
                form_data=other_identifier_form,
                caais_key='identifier_type',
                section=curr_section)
            # 1.2.2 Identifier Value
            other_identifier['identifier_value'] = get_optional_field(
                form_data=other_identifier_form,
                caais_key='identifier_value',
                section=curr_section)
            # 1.2.3 Identifier Note
            other_identifier['identifier_note'] = get_optional_field(
                form_data=other_identifier_form,
                caais_key='identifier_note',
                section=curr_section)
            curr_tree['identifiers'].append(other_identifier)
    # 1.4 Accession Title
    curr_tree['accession_title'] = get_mandatory_field(
        form_data=form_data,
        caais_key='accession_title',
        section=curr_section)
    # 1.5 Archival Unit - Technically Repeatable, but we only send one and possibly not a correct one.
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
    # 2.1.1 Source Type
    curr_tree['source_type'] = str(get_optional_field(
        form_data=form_data,
        caais_key='source_type',
        section=curr_section))
    # 2.1.2 Source Name - Mandatory
    curr_tree['source_name'] = get_mandatory_field(
        form_data=form_data,
        caais_key='source_name',
        section=curr_section)
    # 2.1.3 Source Contact Information - Mandatory
    # The following fields up to 2.1.4 are technically not in the standard
    curr_tree['contact_name'] = get_mandatory_field(
        form_data=form_data,
        caais_key='contact_name',
        section=curr_section)
    curr_tree['job_title'] = get_mandatory_field(
        form_data=form_data,
        caais_key='job_title',
        section=curr_section)
    curr_tree['phone_number'] = get_mandatory_field(
        form_data=form_data,
        caais_key='phone_number',
        section=curr_section)
    curr_tree['email_address'] = get_mandatory_field(
        form_data=form_data,
        caais_key='email',
        section=curr_section)
    curr_tree['address_line_1'] = get_mandatory_field(
        form_data=form_data,
        caais_key='address_line_1',
        section=curr_section)
    curr_tree['address_line_2'] = get_optional_field(
        form_data=form_data,
        caais_key='address_line_2',
        section=curr_section)
    curr_tree['city'] = get_mandatory_field(
        form_data=form_data,
        caais_key='city',
        section=curr_section)
    curr_tree['region'] = get_mandatory_field(
        form_data=form_data,
        caais_key='province_or_state',
        section=curr_section)
    if curr_tree['region'].lower() == 'other':
        curr_tree['region'] = get_optional_field(
            form_data=form_data,
            caais_key='other_province_or_state',
            section=curr_section)
    curr_tree['postal_or_zip_code'] = get_mandatory_field(
        form_data=form_data,
        caais_key='postal_or_zip_code',
        section=curr_section)
    curr_tree['country'] = get_mandatory_field(
        form_data=form_data,
        caais_key='country',
        section=curr_section)
    # 2.1.4 Source Role - Mandatory
    curr_tree['source_role'] = str(get_mandatory_field(
        form_data=form_data,
        caais_key='source_role',
        section=curr_section))
    # 2.1.5 Source Note - Optional
    curr_tree['source_note'] = get_optional_field(
        form_data=form_data,
        caais_key='source_note',
        section=curr_section)
    # 2.2 Custodial History
    curr_tree['custodial_history'] = get_optional_field(
        form_data=form_data,
        caais_key='custodial_history',
        section=curr_section)
    return curr_tree


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
        section=curr_section)
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


def _get_section_4_tree(form_data: dict) -> OrderedDict:
    ''' Convert a nested structure for section 4 of CAAIS from the form.

    Args:
        form_data (dict): The full, cleaned, form data dictionary

    Returns:
        (OrderedDict): A nested structure representing section 4 of CAAIS
    '''
    curr_tree = OrderedDict()
    curr_section = 'section_4'
    # 4.1 Storage Location - Repeatable but we only add one currently.
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
    # 4.3 Material Assessment Statement - Repeatable
    curr_tree['material_assessments'] = []
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
    # 4.3.3 Material Assessment Statement Plan
    new_assessment['material_assessment_statement_plan'] = get_optional_field(
        form_data=form_data,
        caais_key='material_assessment_statement_plan',
        section=curr_section)
    # 4.3.4 Material Assessment Statement Note
    new_assessment['material_assessment_statement_note'] = get_optional_field(
        form_data=form_data,
        caais_key='material_assessment_statement_note',
        section=curr_section)
    curr_tree['material_assessments'].append(new_assessment)
    # Possible Contact Assessment as a second Material Assessment section.
    condition_assessment = get_optional_field(
        form_data=form_data,
        caais_key='condition_assessment',
        section=curr_section
    )
    if len(condition_assessment) > 0:
        physical_assessment = OrderedDict()
        physical_assessment['material_assessment_statement_type'] = 'Contact assessment'
        physical_assessment['material_assessment_statement_value'] = condition_assessment
        curr_tree['material_assessments'].append(physical_assessment)

    # 4.4 Appraisal Statement
    curr_tree['appraisal_statement'] = []
    # 4.5 Associated Documentation
    curr_tree['associated_documentation'] = []
    return curr_tree


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
    # Date is set to now() when the record is added.
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
    # Date is set to now() when the record is added.
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


def _get_property_fields(form_data: dict, section_name: str) -> dict:
    property_fields = {
        'section_1': [
            'repository',
            'accession_title',
            'acquisition_method',
            'custodial_history',
            'disposition_authority',
            'status',
        ],
        'section_2': [
            'source_name',
            'contact_name',
            'job_title',
            'phone_number',
            'email_address',
            'address_line_1',
            'address_line_2',
            'city',
            'region',
            'postal_or_zip_code',
            'country',
            'source_note',
        ],
        'section_4': [
            'storage_location',
            'rights_statement',
            'material_assessment_statement',
            'condition_assessment',
        ]
    }
    return {f: v for f, v in form_data.items() if f in property_fields[section_name]}


def convert_form_data_to_metadata(form_data: dict) -> c_models.Metadata:
    arranged_data = convert_transfer_form_to_meta_tree(form_data)
    metadata = _convert_form_to_caais_section_1(arranged_data['section_1'])
    _convert_form_to_caais_section_2(metadata, arranged_data['section_2'])
    _convert_form_to_caais_section_3(metadata, arranged_data['section_3'])
    _convert_form_to_caais_section_4(metadata, arranged_data['section_4'])
    _convert_form_to_caais_section_5(metadata, arranged_data['section_5'])
    _convert_form_to_caais_section_6(metadata, arranged_data['section_6'])
    _convert_form_to_caais_section_7(metadata, arranged_data['section_7'])
    return metadata


def _convert_form_to_caais_section_1(form_data: dict) -> c_models.Metadata:
    """ Convert form data into the top-level Metadata model and any necessary
    associated models.

    Args:
        form_data (dict): The section 1 form data

    Return: The top-level metadata object.
    """
    # Make the main CAAIS object
    section_1_data = _get_property_fields(form_data, 'section_1')
    # 1.1 Repository, 1.3 Accession Title & 1.5 Acquisition Method as properties.
    metadata = c_models.Metadata.objects.create(**section_1_data)
    # 1.2 Create identifiers.
    for identifier in form_data['identifiers']:
        if len(identifier['identifier_type']) > 0 or len(identifier['identifier_value']) > 0 or \
                len(identifier['identifier_note']) > 0:
            identifier['metadata'] = metadata
            c_models.Identifier.objects.create(**identifier)
    # 1.4 Archival Unit, if it exists.
    if form_data['archival_unit']:
        c_models.ArchivalUnit.objects.create(**{
            'metadata': metadata,
            'archival_unit': form_data['archival_unit']
        })
    if form_data['disposition_authority'] and len(form_data['disposition_authority']) > 0:
        metadata.disposition_authority = form_data['disposition_authority']
        metadata.save()
    return metadata


def _convert_form_to_caais_section_2(metadata: c_models.Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 2 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 2 form data.
    """
    # 2.1 Source of Material
    fields = _get_property_fields(form_data, 'section_2')
    fields['metadata'] = metadata
    source = c_models.SourceOfMaterial.objects.create(**fields)
    s_type = c_models.SourceType.objects.filter(name__iexact=form_data['source_type']).first()
    if s_type is None:
        s_type = c_models.SourceType()
        s_type.name = form_data['source_type']
        s_type.save()
    source.source_type = s_type
    role = c_models.SourceRole.objects.filter(name__iexact=form_data['source_role']).first()
    if role is None:
        role = c_models.SourceRole()
        role.name = form_data['source_role']
        role.save()
    source.source_role = role
    source.save()
    if form_data['custodial_history'] is not None and len(form_data['custodial_history']) > 0:
        # 2.2 Preliminary Custodial History
        metadata.custodial_history = form_data['custodial_history']
        metadata.save()


def _convert_form_to_caais_section_3(metadata: c_models.Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 3 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 3 form data.
    """
    # 3.1 Date of Material (stored on the main Metadata)
    metadata.date_of_material = form_data['date_of_material']
    metadata.save()
    for extent in form_data['extent_statement']:
        # 3.2 Extent Statement
        # We generate a single Extent Statement with only the type, quantity and units and a note.
        statement = c_models.ExtentStatement()
        statement.metadata = metadata
        # 3.2.1 Extent type, try to reuse existing entries.
        ext_type = c_models.ExtentType.objects.filter(name=extent['extent_statement_type']).first()
        if ext_type is None:
            ext_type = c_models.ExtentType()
            ext_type.name = extent['extent_statement_type']
            ext_type.save()
        statement.extent_type = ext_type
        # 3.2.2 Quantity and Unit of Measure
        statement.quantity_and_type_of_units = extent['quantity_and_type_of_units']
        # 3.2.3 Extent Note
        statement.extent_note = extent['extent_statement_note']
        statement.save()
    # 3.3 Scope and Content
    if form_data['scope_and_content'] is not None and len(form_data['scope_and_content']) > 0:
        metadata.scope_and_content = form_data['scope_and_content']
        metadata.save()

    # 3.4 Language of Material
    # Split languages on comma and standardize as lowercase in the database.
    # langs = [x.strip().lower() for x in form_data['language_of_material'].split(',')]
    # for lang in langs:
    c_models.LanguageOfMaterial.objects.create(**{
        'metadata': metadata,
        'language_of_material': form_data['language_of_material']
    })


def _convert_form_to_caais_section_4(metadata: c_models.Metadata, form_data: dict):
    """ Convert form data into any necessary models for section 4 of the CAAIS model.

    Args:
        metadata (Metadata): The main Metadata object for this form submission.
        form_data (dict): The section 4 form data.
    """
    # 4 Management Information Section
    # 4.1 Storage Location - Currently no entry point for location
    # TODO: This currently creates a new record with 'Placeholder' for every submission, do we need this?
    c_models.StorageLocation.objects.create(**{
        'storage_location': form_data['storage_location'],
        'metadata': metadata,
    })
    # 4.2 Rights
    for rights_statement in form_data['rights_statement']:
        right = c_models.Rights()
        right.metadata = metadata
        # 4.2.1 Rights Type
        rights_statement_type = rights_statement['rights_statement_type'] if \
            rights_statement['rights_statement_type'] != 'Other' else rights_statement['other_rights_statement_type']
        rights_type = c_models.RightsType.objects.filter(name__iexact=rights_statement_type).first()
        if not rights_type:
            rights_type = c_models.RightsType()
            rights_type.name = rights_statement_type
            rights_type.save()
        right.rights_type = rights_type
        # 4.1.2 Rights Value
        right.rights_value = rights_statement['rights_statement_value']
        # 4.1.3 Rights Note
        right.rights_note = rights_statement['rights_statement_note']
        right.save()
    # 4.3 Material Assessment Statements
    for preservation_requirement in form_data['material_assessments']:
        requirement_type = c_models.MaterialAssessmentType.objects\
            .filter(name__iexact=preservation_requirement['material_assessment_statement_type']).first()
        if not requirement_type:
            requirement_type = c_models.MaterialAssessmentType()
            requirement_type.name = preservation_requirement['material_assessment_statement_type']
            requirement_type.save()
        mas = c_models.MaterialAssessmentStatement.objects.create(**{
            'metadata': metadata,
            'assessment_type': requirement_type,
            'assessment_value': preservation_requirement['material_assessment_statement_value'],
        })
        try:
            if len(preservation_requirement['material_assessment_statement_note']) > 0:
                mas.assessment_note = preservation_requirement['material_assessment_statement_note']
        except KeyError:
            pass
        try:
            if len(preservation_requirement['material_assessment_statement_plan']) > 0:
                mas.assessment_plan = preservation_requirement['material_assessment_statement_plan']
        except KeyError:
            pass
        mas.save()


def _convert_form_to_caais_section_5(metadata: c_models.Metadata, form_data: dict):
    for event in form_data['event_statement']:
        # 5.1.1 Event Type
        event_type = c_models.EventType.objects.filter(name__iexact=event['event_type']).first()
        if event_type is None:
            event_type = c_models.EventType()
            event_type.name = event['event_type']
            event_type.save()
        # 5.1.2 Event Date - Date is set to now() on record add.
        # 5.1.3 Event Agent
        # 5.1.4 Event Note
        c_models.Event.objects.create(**{
            'metadata': metadata,
            'event_type': event_type,
            'event_agent': event['event_agent'],
            'event_note': event['event_note']
        })


def _convert_form_to_caais_section_6(metadata: c_models.Metadata, form_data: dict):

    if len(form_data['general_note']) > 0:
        c_models.GeneralNote.objects.create(**{
            'note': form_data['general_note'],
            'metadata': metadata
        })


def _convert_form_to_caais_section_7(metadata: c_models.Metadata, form_data: dict):
    # 7.1 Rules or Conventions (static value currently)
    if len(form_data['rules_or_conventions']) > 0:
        metadata.rules_or_conventions = form_data['rules_or_conventions']
    # 7.2 Level of Detail (no value)
    if len(form_data['level_of_detail']) > 0:
        metadata.level_of_detail = form_data['level_of_detail']
    # 7.4 Language of Accession Record
    if len(form_data['language_of_accession_record']) > 0:
        metadata.language_of_record = form_data['language_of_accession_record']
    metadata.save()
    # 7.3 Date of Creation or Revision - Technically repeatable, but we only include one array item
    for revision in form_data['date_of_creation_or_revision']:
        # 7.3.1 Action Type
        revision_type = c_models.DateOfCreationOrRevisionType.objects.filter(name__iexact=revision['action_type'])\
            .first()
        if revision_type is None:
            revision_type = c_models.DateOfCreationOrRevisionType.objects.create(**{
                'name': revision['action_type']
            })
        c_models.DateOfCreationOrRevision.objects.create(**{
            'metadata': metadata,
            'action_type': revision_type,
            'action_agent': revision['action_agent'],
            'action_note': revision['action_note']
        })


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
