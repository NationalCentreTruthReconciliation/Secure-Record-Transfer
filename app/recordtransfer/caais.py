"""Converts the transfer form to a :py:class:`caais.models.Metadata` object.

To set default values, refer to :ref:`Data Formatting and Defaults`.
"""

import logging
from typing import Optional, Type

from caais.models import *
from django.conf import settings
from django.db.models import Model
from django.utils.translation import gettext

LOGGER = logging.getLogger("recordtransfer")


get_setting_name = lambda field_name: f"CAAIS_DEFAULT_{field_name.upper().strip()}"
get_setting_name.__doc__ = """Generates a setting name in the :py:data:`django.conf.settings`
object that may contain a default value for some field.

Args:
    field_name (str): The name of the field on the model or the form

Returns:
    (str): A setting name for the default value, in the form CAAIS_DEFAULT_FIELD_NAME
"""


def map_form_to_metadata(form_data: dict) -> Metadata:
    """Convert cleaned form data to a :py:class:`caais.models.Metadata` object.
    Form fields are expected to exactly match field names in CAAIS models.

    Related CAAIS defaults:

    - :ref:`CAAIS_DEFAULT_REPOSITORY`
    - :ref:`CAAIS_DEFAULT_ACCESSION_TITLE`
    - :ref:`CAAIS_DEFAULT_ACQUISITION_METHOD`
    - :ref:`CAAIS_DEFAULT_STATUS`
    - :ref:`CAAIS_DEFAULT_DATE_OF_MATERIALS`
    - :ref:`CAAIS_DEFAULT_RULES_OR_CONVENTIONS`
    - :ref:`CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD`

    Args:
        form_data (dict): Cleaned form data from form

    Returns:
        (Metadata): The metadata created from the form data
    """
    metadata = Metadata(
        repository=str_or_default(form_data, "repository"),
        accession_title=str_or_default(form_data, "accession_title"),
        acquisition_method=term_or_default(form_data, "acquisition_method", AcquisitionMethod),
        status=term_or_default(form_data, "status", Status),
        date_of_materials=str_or_default(form_data, "date_of_materials"),
        date_is_approximate=form_data.get("date_is_approximate", False),
        rules_or_conventions=str_or_default(form_data, "rules_or_conventions"),
        language_of_accession_record=str_or_default(form_data, "language_of_accession_record"),
    )
    metadata.save()

    # Simple cases that do not require special logic
    add_related_models(form_data, metadata, ArchivalUnit)
    add_related_models(form_data, metadata, DispositionAuthority)
    add_related_models(form_data, metadata, PreliminaryCustodialHistory)
    add_related_models(form_data, metadata, ExtentStatement)
    add_related_models(form_data, metadata, PreliminaryScopeAndContent)
    add_related_models(form_data, metadata, LanguageOfMaterial)
    add_related_models(form_data, metadata, StorageLocation)
    add_related_models(form_data, metadata, PreservationRequirements)
    add_related_models(form_data, metadata, Appraisal)
    add_related_models(form_data, metadata, AssociatedDocumentation)
    add_related_models(form_data, metadata, GeneralNote)

    # Complex cases that require special logic
    add_identifiers(form_data, metadata)
    add_source_of_materials(form_data, metadata)
    add_rights(form_data, metadata)

    # Special cases that do not depend on the form's data
    add_submission_event(metadata)
    add_date_of_creation(metadata)

    return metadata


def add_identifiers(form_data: dict, metadata: Metadata) -> None:
    """Populate metadata with :py:class:`caais.models.Identifier` objects.

    No related CAAIS defaults.

    Args:
        form_data (dict): The form data dictionary
        metadata (Metadata): The top-level metadata object to link any new objects to
    """
    formset_key = "formset-otheridentifiers"

    if formset_key not in form_data or not any(form_data[formset_key]):
        return

    already_created = set()

    for i, other_identifier_form in enumerate(form_data[formset_key], 0):
        if not other_identifier_form:
            continue

        identifier_type = other_identifier_form.get("other_identifier_type", "")
        identifier_value = other_identifier_form.get("other_identifier_value", "")
        identifier_note = other_identifier_form.get("other_identifier_note", "")

        id_tuple = (identifier_type, identifier_value, identifier_note)

        if not any(id_tuple):
            LOGGER.warning(
                ('All identifier fields were empty for form index %d of formset "%s"'),
                i,
                formset_key,
            )

        elif id_tuple not in already_created:
            Identifier.objects.create(
                metadata=metadata,
                identifier_type=identifier_type,
                identifier_value=identifier_value,
                identifier_note=identifier_note,
            )
            already_created.add(id_tuple)

        else:
            LOGGER.warning('Duplicate identifier was ignored: "%s"', repr(id_tuple))


def add_source_of_materials(form_data: dict, metadata: Metadata) -> None:
    """Populate metadata with :py:class:`SourceOfMaterial` objects

    Related CAAIS defaults:

    - :ref:`CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY`

    Args:
        form_data (dict): The form data dictionary
        metadata (Metadata): The top-level metadata object to link any new objects to
    """
    notes = []

    source_type = coalesce_other_term_field(
        form_data, "source_type", TermClass=SourceType, notes=notes
    )
    source_role = coalesce_other_term_field(
        form_data, "source_role", TermClass=SourceRole, notes=notes
    )

    source_note = str_or_default(form_data, "source_note")

    if source_note:
        notes.append(source_note)

    source_note = ". ".join(notes)

    source_name = form_data.get("source_name", "")
    contact_name = form_data.get("contact_name", "")
    job_title = form_data.get("job_title", "")
    organization = form_data.get("organization", "")
    phone_number = form_data.get("phone_number", "")
    email_address = form_data.get("email", "")
    address_line_1 = form_data.get("address_line_1", "")
    address_line_2 = form_data.get("address_line_2", "")
    city = form_data.get("city", "")

    if form_data.get("other_province_or_state", ""):
        region = form_data["other_province_or_state"]
    else:
        region = form_data.get("province_or_state", "")

    postal_or_zip_code = form_data.get("postal_or_zip_code", "")
    country = form_data.get("country", None)

    source_confidentiality = term_or_default(
        form_data, "source_confidentiality", SourceConfidentiality
    )

    if not any(
        [
            source_type,
            source_name,
            contact_name,
            job_title,
            organization,
            phone_number,
            email_address,
            address_line_1,
            address_line_2,
            city,
            region,
            postal_or_zip_code,
            country,
            source_role,
            source_note,
            source_confidentiality,
        ]
    ):
        LOGGER.warning("All source of material fields and defaults were empty")
        return

    SourceOfMaterial.objects.create(
        metadata=metadata,
        source_type=source_type,
        source_name=source_name,
        contact_name=contact_name,
        job_title=job_title,
        organization=organization,
        phone_number=phone_number,
        email_address=email_address,
        address_line_1=address_line_1,
        address_line_2=address_line_2,
        city=city,
        region=region,
        postal_or_zip_code=postal_or_zip_code,
        country=country,
        source_role=source_role,
        source_note=source_note,
        source_confidentiality=source_confidentiality,
    )


def add_rights(form_data: dict, metadata: Metadata):
    """Populate metadata with Rights objects

    No related CAAIS defaults.

    Args:
        form_data (dict): The form data dictionary
        metadata (Metadata): The top-level metadata object to link any new objects to
    """
    formset_key = "formset-rights"

    if formset_key not in form_data or not any(form_data[formset_key]):
        return

    already_created = set()

    for i, rights_form in enumerate(form_data[formset_key], 0):
        if not rights_form:
            continue

        notes = []

        rights_type = coalesce_other_term_field(
            rights_form, "rights_type", TermClass=RightsType, notes=notes
        )
        rights_value = rights_form.get("rights_value", "")
        rights_note = rights_form.get("rights_note", "")

        if rights_note:
            notes.append(rights_note)

        rights_note = ". ".join(notes)

        id_tuple = (rights_type, rights_value, rights_note)

        if not any(id_tuple):
            LOGGER.warning(
                ('All rights fields were empty for form index %d of formset "%s"'), i, formset_key
            )

        elif id_tuple not in already_created:
            Rights.objects.create(
                metadata=metadata,
                rights_type=rights_type,
                rights_value=rights_value,
                rights_note=rights_note,
            )
            already_created.add(id_tuple)

        else:
            LOGGER.warning("Duplicate rights were ignored: %s", repr(id_tuple))


def add_submission_event(metadata: Metadata):
    """Populate metadata with a new Submission-type Event object

    Related CAAIS defaults:

    - :ref:`CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE` (Required)
    - :ref:`CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT`
    - :ref:`CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE`

    Args:
        metadata (Metadata): The top-level metadata object to link any new objects to
    """
    # The CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE is guaranteed to have a value
    submission_type_name = settings.CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE

    event_type, created = EventType.objects.get_or_create(name=submission_type_name)

    if created:
        LOGGER.info(
            ('Created new %s term with name "%s"'),
            EventType.__class__.__name__,
            submission_type_name,
        )

    event_agent = getattr(settings, "CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT", "")
    event_note = getattr(settings, "CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE", "")

    Event.objects.create(
        metadata=metadata,
        event_type=event_type,
        event_agent=event_agent,
        event_note=event_note,
    )


def add_date_of_creation(metadata: Metadata):
    """Populate metadata with a new Creation-type DateOfCreationOrRevision object

    Related CAAIS defaults:

    - :ref:`CAAIS_DEFAULT_CREATION_TYPE` (Required)
    - :ref:`CAAIS_DEFAULT_CREATION_AGENT`
    - :ref:`CAAIS_DEFAULT_CREATION_NOTE`

    Args:
        metadata (Metadata): The top-level metadata object to link any new objects to
    """
    # The CAAIS_DEFAULT_CREATION_TYPE is guaranteed to have a value
    creation_type_name = settings.CAAIS_DEFAULT_CREATION_TYPE

    creation_type, created = CreationOrRevisionType.objects.get_or_create(name=creation_type_name)

    if created:
        LOGGER.info(
            ('Created new %s term with name "%s"'),
            CreationOrRevisionType.__class__.__name__,
            creation_type_name,
        )

    creation_agent = getattr(settings, "CAAIS_DEFAULT_CREATION_AGENT", "")
    creation_note = getattr(settings, "CAAIS_DEFAULT_CREATION_NOTE", "")

    DateOfCreationOrRevision.objects.create(
        metadata=metadata,
        creation_or_revision_type=creation_type,
        creation_or_revision_agent=creation_agent,
        creation_or_revision_note=creation_note,
    )


################################################################################
#
# --- HELPER FUNCTIONS ---
#


def add_related_models(form_data: dict, metadata: Metadata, CaaisModel: Model):
    """Add up to one related model to the metadata object by mapping the
    model's fields to the form's fields. For every field on the model that is
    not named "metadata" or "id," a field with the same name is searched in the
    form. If that field exists in both the form and the model, then the data
    from the form is passed to the model when it is created.

    If the model has relational fields that are not to a metadata object or to
    an :py:class:`~caais.models.AbstractTerm`, then a :code:`ValueError` is thrown.

    Default values can be set by creating settings in
    the module set by DJANGO_SETTINGS_MODULE named CAAIS_DEFAULT_FIELD_NAME, where
    FIELD_NAME is the uppercase-d field name of the model and the form field.

    Args:
        form_data (dict): The cleaned form data dictionary
        metadata (Metadata): The top-level metadata object to link any new objects to
        CaaisModel (Model): A model from caais.models
    """
    model_field_data = {}

    for field in filter(lambda f: f.name not in ("id", "metadata"), CaaisModel._meta.get_fields()):
        # Populate terms
        if field.is_relation:
            if not issubclass(field.related_model, AbstractTerm):
                raise ValueError(
                    f"Could not handle related model {repr(field.related_model)}! "
                    f"Can only handle {repr(AbstractTerm)}"
                )

            term = term_or_default(
                form_data, field.name, TermClass=field.related_model, default=None
            )

            if term:
                model_field_data[field.name] = term

        # Populate other fields
        else:
            data = str_or_default(form_data, field.name, default="")

            if data:
                model_field_data[field.name] = data

    if not model_field_data:
        return

    CaaisModel.objects.create(metadata=metadata, **model_field_data)


def str_or_default(form_data: dict, field_name: str, default: str = ""):
    """Return form data if it exists, or the setting in the :py:data:`django.conf.settings` object
    if it exists, or the default value, in that order of priority.

    Args:
        form_data (dict):
            The cleaned data from the transfer form
        field_name (str):
            The name of the field in the form data
        default (str):
            The default value to return if the data does not exist in the form
            or is empty, and if the setting also does not exist or is empty.

    Returns:
        (str):
            The data from the form, or the value from the setting, or the default
            value, in order of priority returned.
    """
    return (
        form_data.get(field_name, "")
        or getattr(settings, get_setting_name(field_name), "")
        or default
    )


def term_or_default(
    form_data: dict,
    field_name: str,
    TermClass: Type[AbstractTerm],
    default: Optional[AbstractTerm] = None,
) -> Optional[AbstractTerm]:
    """If the name of a term can be found in the form data or in the
    :py:data:`django.conf.settings` object, return an instance of the term for the given
    TermClass with that name. If the term did not exist, it is created.

    If no name can be found in the form data or in :py:data:`django.conf.settings`,
    the default value is returned.

    Args:
        form_data (dict):
            The cleaned data from the transfer form
        field_name (str):
            The name of the key in the form data
        TermClass (Type[AbstractTerm]):
            The type of term to return if the name exists in the form or in the
            settings
        default (Optional[AbstractTerm]):
            A term (or None) to return if there is no form data or there is no
            default set in :code:`django.conf.settings`

    Returns:
        (Optional[AbstractTerm]):
            A term instance, if the name of the term could be found, or the
            default if not
    """
    name = str_or_default(form_data, field_name, default="")
    if not name:
        return default
    term, created = TermClass.objects.get_or_create(name=name)
    if created:
        LOGGER.info('Created new %s term with name "%s"', TermClass.__name__, name)
    return term


def coalesce_other_term_field(
    form_data: dict, field_name: str, TermClass: Type[AbstractTerm], notes: Optional[list] = None
) -> Optional[AbstractTerm]:
    """Attempt to coalesce an other_<TERM FIELD> field into a term, if a term
    does not already exist.

    There are two cases:

    - term is the Other Term, and other_term is filled
    - term is not the Other Term
    """
    term = form_data.get(field_name, None)
    other_term = form_data.get(f"other_{field_name}", "")

    if not term and not other_term:
        return None

    if term.name.lower().strip() != "other" and other_term:
        LOGGER.warning(
            ("Both %s (%s) and other_%s (%s) were specified. Ignoring the latter"),
            field_name,
            repr(term),
            field_name,
            repr(other_term),
        )

    elif other_term:
        try:
            term = TermClass.objects.get(name=other_term)
            LOGGER.info(
                ("Found existing %s for other_%s: %s"), TermClass.__name__, field_name, repr(term)
            )

        except TermClass.DoesNotExist:
            if isinstance(notes, list):
                notes.append(
                    gettext(f"{TermClass._meta.verbose_name} was noted as {repr(other_term)}")
                )

    return term
