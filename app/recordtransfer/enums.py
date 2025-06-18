from enum import Enum
from typing import NamedTuple, Optional

from django.db import models
from django.utils.translation import gettext_lazy as _


class SubmissionStep(Enum):
    """Steps in the multi-stage submission form, listed in the order they should be completed.
    Note that the final step is either "uploadfiles" or "finalnotes" depending on the
    configuration.
    """

    ACCEPT_LEGAL = "acceptlegal"
    CONTACT_INFO = "contactinfo"
    SOURCE_INFO = "sourceinfo"
    RECORD_DESCRIPTION = "recorddescription"
    RIGHTS = "rights"
    OTHER_IDENTIFIERS = "otheridentifiers"
    GROUP_SUBMISSION = "groupsubmission"
    UPLOAD_FILES = "uploadfiles"
    FINAL_NOTES = "finalnotes"
    REVIEW = "review"


class SiteSettingType(models.TextChoices):
    """The type of the setting value."""

    INT = "int", _("Integer")
    STR = "str", _("String")


class SettingKeyMeta(NamedTuple):
    """Describes a setting's type, description, and default value."""

    value_type: SiteSettingType
    description: str
    default_value: Optional[str] = None


class SiteSettingKey(Enum):
    """The keys for the site settings. These keys are used to store and retrieve settings from
    the database.
    """

    # Emails
    ARCHIVIST_EMAIL = SettingKeyMeta(
        SiteSettingType.STR,
        _("The email displayed for people to contact an archivist."),
        default_value="archivist@example.com",
    )
    DO_NOT_REPLY_USERNAME = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            'A username for the application to send "do not reply" emails from. This '
            "username is combined with the site's base URL to create an email address. "
            "The URL can be set from the admin site."
        ),
        default_value="do-not-reply",
    )

    # Pagination
    PAGINATE_BY = SettingKeyMeta(
        SiteSettingType.INT,
        _(
            "This setting controls how many rows of items are shown per page in tables "
            "that support pagination."
        ),
        default_value="10",
    )

    # CAAIS defaults
    CAAIS_DEFAULT_REPOSITORY = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 1.1 - Repository."),
    )
    CAAIS_DEFAULT_ACCESSION_TITLE = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 1.3 - Accession Title"),
    )
    CAAIS_DEFAULT_ARCHIVAL_UNIT = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 1.4 - Archival Unit.\n"
            "While the Archival Unit field is repeatable in CAAIS, it is not possible to "
            "specify multiple archival unit defaults."
        ),
    )
    CAAIS_DEFAULT_DISPOSITION_AUTHORITY = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 1.6 - Disposition Authority.\n"
            "While the Disposition Authority field is repeatable, it is not possible to "
            "specify multiple disposition authority defaults."
        ),
    )
    CAAIS_DEFAULT_ACQUISITION_METHOD = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 1.5 - Acquisition Method"),
    )
    CAAIS_DEFAULT_STATUS = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 1.7 - Status.\n"
            "Leave empty, or populate with a term like 'Waiting for review' to signify "
            "that the metadata has not been reviewed yet."
        ),
    )
    CAAIS_DEFAULT_SOURCE_CONFIDENTIALITY = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 2.1.6 - Source Confidentiality.\n"
            "If a default is supplied, the source confidentiality will be applied to every "
            "source of material received."
        ),
    )
    CAAIS_DEFAULT_PRELIMINARY_CUSTODIAL_HISTORY = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 2.2 - Preliminary Custodial History.\n"
            "While the Preliminary Custodial History field is repeatable in CAAIS, it is not "
            "possible to specify multiple defaults here."
        ),
    )
    CAAIS_DEFAULT_DATE_OF_MATERIALS = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 3.1 - Date of Materials"),
    )
    CAAIS_DEFAULT_EXTENT_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.2.1 - Extent Type.\n"
            "If a default is supplied, the extent type will be applied to every extent "
            "statement received."
        ),
    )
    CAAIS_DEFAULT_QUANTITY_AND_UNIT_OF_MEASURE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.2.2 - Quantity and Unit of Measure.\n"
            "If a default is supplied, the quantity and unit of measure will be applied to every "
            "extent statement received."
        ),
    )
    CAAIS_DEFAULT_CONTENT_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.2.3 - Content Type.\n"
            "If a default is supplied, the content type will be applied to every extent "
            "statement received."
        ),
    )
    CAAIS_DEFAULT_CARRIER_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.2.4 - Carrier Type.\n"
            "If a default is supplied, the carrier type will be applied to every extent "
            "statement received."
        ),
    )
    CAAIS_DEFAULT_EXTENT_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.2.5 - Extent Note.\n"
            "If a default is supplied, the extent note will be applied to every extent "
            "statement received."
        ),
    )
    CAAIS_DEFAULT_PRELIMINARY_SCOPE_AND_CONTENT = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 3.3 - Preliminary Scope and "
            "Content.\nWhile the Preliminary Scope and Content field is repeatable in CAAIS, "
            "it is not possible to specify multiple defaults here."
        ),
    )
    CAAIS_DEFAULT_LANGUAGE_OF_MATERIAL = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 3.4 - Language of Material"),
    )
    CAAIS_DEFAULT_STORAGE_LOCATION = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 4.1 - Storage Location"),
    )
    CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.3.1 - Preservation "
            "Requirements Type.\nIf not empty, a default preservation requirements statement "
            "will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_VALUE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.3.2 - Preservation "
            "Requirements Value.\nIf not empty, a default preservation requirements statement "
            "will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_PRESERVATION_REQUIREMENTS_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.3.3 - Preservation "
            "Requirements Note.\nIf not empty, a default preservation requirements statement "
            "will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_APPRAISAL_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.4.1 - Appraisal Type.\n"
            "If not empty, a default appraisal statement will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_APPRAISAL_VALUE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.4.2 - Appraisal Value.\n"
            "If not empty, a default appraisal statement will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_APPRAISAL_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.4.3 - Appraisal Note.\n"
            "If not empty, a default appraisal statement will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.5.1 - Associated "
            "Documentation Type.\n"
            "If not empty, a default associated document will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_TITLE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.5.2 - Associated "
            "Documentation Title.\n"
            "If not empty, a default associated document will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_ASSOCIATED_DOCUMENTATION_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default value to fill in metadata for CAAIS sec. 4.5.3 - Associated "
            "Documentation Note.\n"
            "If not empty, a default associated document will be applied to each submission."
        ),
    )
    CAAIS_DEFAULT_GENERAL_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 6.1 - General Note"),
    )
    CAAIS_DEFAULT_RULES_OR_CONVENTIONS = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 7.1 - Rules or Conventions"),
    )
    CAAIS_DEFAULT_LANGUAGE_OF_ACCESSION_RECORD = SettingKeyMeta(
        SiteSettingType.STR,
        _("Default value to fill in metadata for CAAIS sec. 7.3 - Language of Accession Record"),
    )
    # CAAIS event defaults
    CAAIS_DEFAULT_SUBMISSION_EVENT_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default submission event type name - related to CAAIS sec. 5.1.1.\n"
            "At the time of receiving a submission, a 'Submission' type event is created "
            "for the submission. You can control the Event Type name for that event here."
        ),
        default_value="Transfer Submitted",
    )
    CAAIS_DEFAULT_SUBMISSION_EVENT_AGENT = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default submission event agent - related to CAAIS sec. 5.1.3.\n"
            "At the time of receiving a submission, a 'Submission' type event is created "
            "for the submission. You can control the Event Agent's name for that event here."
        ),
    )
    CAAIS_DEFAULT_SUBMISSION_EVENT_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default submission event note - related to CAAIS sec. 5.1.4.\n"
            "At the time of receiving a submission, a 'Submission' type event is created "
            "for the submission. You can control whether an Event Note is added for the event here."
        ),
    )
    # CAAIS creation defaults
    CAAIS_DEFAULT_CREATION_TYPE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default date of creation event name - related to CAAIS sec. 7.2.1.\n"
            "At the time of receiving a submission, a Date of Creation or Revision is created "
            "to indicate the date the accession record was created. You can control the name "
            "of the event here if you do not want to call it 'Creation'."
        ),
        default_value="Creation",
    )
    CAAIS_DEFAULT_CREATION_AGENT = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default date of creation event agent - related to CAAIS sec. 7.2.3.\n"
            "At the time of receiving a submission, a Date of Creation or Revision is created "
            "to indicate the date the accession record was created. You can control the name "
            "of the event agent here."
        ),
    )
    CAAIS_DEFAULT_CREATION_NOTE = SettingKeyMeta(
        SiteSettingType.STR,
        _(
            "Default date of creation event note - related to CAAIS sec. 7.2.4.\n"
            "At the time of receiving a submission, a Date of Creation or Revision is created "
            "to indicate the date the accession record was created. You can add a note to that "
            "event here by setting the value to something other than an empty string."
        ),
    )

    @property
    def key_name(self) -> str:
        """The name of the setting key, used for database storage."""
        return self.name

    @property
    def value_type(self) -> SiteSettingType:
        """The type of the setting value."""
        return self.value.value_type

    @property
    def description(self) -> str:
        """A description of the setting, used for display in the admin interface."""
        return self.value.description

    @property
    def default_value(self) -> Optional[str]:
        """The default value for the setting, used if no value is set in the database."""
        return self.value.default_value
