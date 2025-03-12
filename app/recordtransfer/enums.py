from enum import Enum


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
    GROUP_TRANSFER = "grouptransfer"
    UPLOAD_FILES = "uploadfiles"
    FINAL_NOTES = "finalnotes"
    REVIEW = "review"
