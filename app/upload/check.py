import contextlib
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Union

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext, ngettext_lazy
from django.utils.translation import gettext_lazy as _

from upload.constants import WindowsFileRestrictions
from upload.mime import MAGIC_AVAILABLE, mime

# This is to avoid a circular import
if TYPE_CHECKING:
    from upload.models import UploadSession


def accept_file(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Determine if a new file should be accepted.

    Args:
        filename: The name of the file to check
        filesize: The size of the file in bytes
        file: The object containing the file data

    These checks are applied:
    - The file name is safe and not malicious
    - The file name is not empty
    - The file has an accepted extension
    - The file's MIME type matches the expected MIME type for the extension
    - The file's size is an integer greater than zero
    - The file's size is less than or equal to the maximum allowed size for one file

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the session is valid, or False if not. The dictionary also contains
            an 'error' and 'verboseError' key if 'accepted' is False.
    """
    validators = [
        _validate_file_size,
        _validate_basic_filename,
        _validate_filename_characters,
        _validate_absolute_paths,
        _validate_path_traversal,
        _validate_windows_reserved_names,
        _validate_file_extension,
        _validate_mime_type,
    ]

    for validator in validators:
        result = validator(filename, filesize, file)
        if not result["accepted"]:
            if "error" not in result:
                result["error"] = _("Invalid filename or size")
            if "verboseError" not in result:
                result["verboseError"] = result["error"]
            return result

    # All checks succeeded
    return {"accepted": True}


def accept_session(filename: str, filesize: Union[str, int], session: UploadSession) -> dict:
    """Determine if a new file should be accepted as part of the session.

    These checks are applied:
    - The session has room for more files according to the MAX_TOTAL_UPLOAD_COUNT
    - The session has room for more files according to the MAX_TOTAL_UPLOAD_SIZE_MB
    - A file with the same name has not already been uploaded

    Args:
        filename (str): The name of the file
        filesize (Union[str, int]): A string or integer representing the size of
            the file (in bytes)
        session (UploadSession): The session files are being uploaded to

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the session is valid, or False if not. The dictionary also contains
            an 'error' and 'verboseError' key if 'accepted' is False.
    """
    if not session:
        return {"accepted": True}

    # Check number of files is within allowed total
    if session.file_count >= settings.MAX_TOTAL_UPLOAD_COUNT:
        return {
            "accepted": False,
            "error": gettext("You can not upload anymore files."),
            "verboseError": gettext(
                'The file "%(filename)s" would push the total file count past the '
                "maximum number of files (%(max_count)s)"
            )
            % {"filename": filename, "max_count": settings.MAX_TOTAL_UPLOAD_COUNT},
        }

    # Check total size of all files plus current one is within allowed size
    max_size = max(
        settings.MAX_SINGLE_UPLOAD_SIZE_MB,
        settings.MAX_TOTAL_UPLOAD_SIZE_MB,
    )
    max_remaining_size_bytes = mb_to_bytes(max_size) - session.upload_size
    if int(filesize) > max_remaining_size_bytes:
        return {
            "accepted": False,
            "error": gettext("Maximum total upload size (%(max_size)s MB) exceeded")
            % {"max_size": max_size},
            "verboseError": gettext(
                'The file "%(filename)s" would push the total transfer size past the %(max_size)sMB max'
            )
            % {"filename": filename, "max_size": max_size},
        }

    # Check that a file with this name has not already been uploaded
    filename_list = [f.name for f in session.get_temporary_uploads()]
    if filename in filename_list:
        return {
            "accepted": False,
            "error": gettext("A file with the same name has already been uploaded."),
            "verboseError": gettext(
                'A file with the name "%(filename)s" has already been uploaded'
            )
            % {"filename": filename},
        }

    # All checks succeded
    return {"accepted": True}


def _validate_basic_filename(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate basic filename requirements."""
    if not filename or not filename.strip():
        return {
            "accepted": False,
            "error": _("Filename cannot be empty"),
        }

    if len(filename) > WindowsFileRestrictions.MAX_FILENAME_LENGTH:
        return {
            "accepted": False,
            "error": _("Filename is too long"),
            "verboseError": _(
                "Filename is too long (%(num_chars)s characters, max %(max_chars)s is allowed)"
            )
            % {
                "num_chars": len(filename),
                "max_chars": WindowsFileRestrictions.MAX_FILENAME_LENGTH,
            },
        }

    return {"accepted": True}


def _validate_filename_characters(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate filename doesn't contain control characters."""
    if any(ord(char) < 32 for char in filename):
        return {
            "accepted": False,
            "error": _("Filename contains invalid characters"),
        }

    return {"accepted": True}


def _validate_absolute_paths(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate filename doesn't contain absolute path patterns."""
    if filename.startswith("/"):
        return {
            "accepted": False,
            "error": _("Absolute paths are not allowed"),
            "verboseError": _('Filename "%(filename)s" begins with "/"') % {"filename": filename},
        }

    if len(filename) > 2 and filename[1] == ":":
        return {
            "accepted": False,
            "error": _("Absolute paths are not allowed"),
            "verboseError": _('Filename "%(filename)s" begins with "%(drive_letter)s:"')
            % {
                "filename": filename,
                "drive_letter": filename[0],
            },
        }

    return {"accepted": True}


def _validate_path_traversal(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate filename doesn't contain path traversal patterns."""
    decoded_filename = filename

    with contextlib.suppress(Exception):
        decoded_filename = urllib.parse.unquote(filename)

    traversal_patterns = [
        "..",
        "/",
        "\\",
        "%2e%2e",  # URL encoded ..
        "%2f",  # URL encoded /
        "%5c",  # URL encoded \\
        "%252e%252e",  # Double URL encoded ..
        "%252f",  # Double URL encoded /
        "%255c",  # Double URL encoded \\
    ]

    # Create a set, since decoded filename might be the same as the filename
    check_files = {decoded_filename.lower(), filename.lower()}

    for pattern in traversal_patterns:
        if any(pattern in file for file in check_files):
            return {
                "accepted": False,
                "error": _("Filename contains invalid path characters"),
                "verboseError": _(
                    'Filename "%(filename)s" contains invalid character pattern: "%(pattern)s"'
                )
                % {"filename": filename, "pattern": pattern},
            }

    return {"accepted": True}


def _validate_windows_reserved_names(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate filename doesn't use Windows reserved names."""
    base_name = filename.split(".")[0].upper()
    if base_name in WindowsFileRestrictions.RESERVED_FILENAMES:
        return {
            "accepted": False,
            "error": _("Filename uses reserved system name"),
            "verboseError": _(
                'Filename "%(filename)s" includes Windows reserved filename "%(reserved)s"'
            )
            % {
                "filename": filename,
                "reserved": base_name,
            },
        }

    return {"accepted": True}


def _validate_file_extension(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Validate that file extension exists, and is allowed."""
    # Check extension exists
    name_split = filename.split(".")
    if len(name_split) == 1:
        return {
            "accepted": False,
            "error": gettext("File is missing an extension."),
            "verboseError": gettext('The file "%(filename)s" does not have a file extension')
            % {"filename": filename},
        }

    # Check extension is allowed
    extension = name_split[-1].lower()
    if not any(
        extension == accepted_extension.lower()
        for accepted_extensions in settings.ACCEPTED_FILE_FORMATS.values()
        for accepted_extension in accepted_extensions
    ):
        return {
            "accepted": False,
            "error": gettext('Files with "%(extension)s" extension are not allowed.')
            % {"extension": extension},
            "verboseError": gettext(
                'The file "%(filename)s" has an invalid extension (.%(extension)s)'
            )
            % {"filename": filename, "extension": extension},
        }

    return {"accepted": True}


def _validate_mime_type(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Check if the file's MIME type matches the expected MIME type for its extension.

    Only performs validation if magic library is available.
    """
    # If magic library is not available, skip MIME type validation
    if not MAGIC_AVAILABLE:
        return {"accepted": True}

    extension = Path(filename).suffix.lower().lstrip(".")

    # Get expected MIME types for this extension
    expected_mime_types = mime.guess(extension)
    if not expected_mime_types:
        return {
            "accepted": False,
            "error": _("File type is not supported"),
            "verboseError": _(
                'The file "%(filename)s" has an unsupported extension "%(extension)s"'
            )
            % {"filename": filename, "extension": extension},
        }

    # Detect actual MIME type using python-magic
    try:
        detected_mime_type = mime.check(file)
    except Exception:
        return {
            "accepted": False,
            "error": _("File type could not be determined"),
            "verboseError": _(
                'The file "%(filename)s" could not be analyzed for MIME type validation'
            )
            % {"filename": filename},
        }

    # Check if detected MIME type matches any expected MIME type
    if detected_mime_type not in expected_mime_types:
        return {
            "accepted": False,
            "error": ngettext_lazy(
                'File MIME type mismatch. Expected %(expected)s but got "%(detected)s".',
                'File MIME type mismatch. Expected one of: %(expected)s but got "%(detected)s".',
                len(expected_mime_types),
            )
            % {
                "expected": ", ".join(f'"{mtype}"' for mtype in sorted(expected_mime_types)),
                "detected": detected_mime_type,
            },
            "verboseError": ngettext_lazy(
                'The file "%(filename)s" has MIME type "%(detected)s" but expected %(expected)s',
                'The file "%(filename)s" has MIME type "%(detected)s" but expected one of: %(expected)s',
                len(expected_mime_types),
            )
            % {
                "filename": filename,
                "detected": detected_mime_type,
                "expected": ", ".join(f'"{mtype}"' for mtype in sorted(expected_mime_types)),
            },
        }

    return {"accepted": True}


def _validate_file_size(filename: str, filesize: int, file: UploadedFile) -> dict:
    """Check filesize is greater than zero is within the max single upload size."""
    if filesize < 0:
        return {
            "accepted": False,
            "error": gettext("File size is invalid."),
            "verboseError": gettext('The file "%(filename)s" has an invalid size (%(size)s)')
            % {"filename": filename, "size": filesize},
        }
    if filesize == 0:
        return {
            "accepted": False,
            "error": gettext("File is empty."),
            "verboseError": gettext('The file "%(filename)s" is empty') % {"filename": filename},
        }

    # Check file size is less than the maximum allowed size for a single file
    max_single_size = min(
        settings.MAX_SINGLE_UPLOAD_SIZE_MB,
        settings.MAX_TOTAL_UPLOAD_SIZE_MB,
    )
    max_single_size_bytes = mb_to_bytes(max_single_size)
    if filesize > max_single_size_bytes:
        size_mb = bytes_to_mb(filesize)
        return {
            "accepted": False,
            "error": gettext("File is too big (%(size_mb).2fMB). Max filesize: %(max_size_mb)sMB")
            % {"size_mb": size_mb, "max_size_mb": max_single_size},
            "verboseError": gettext(
                'The file "%(filename)s" is too big (%(size_mb).2fMB). Max filesize: %(max_size_mb)sMB'
            )
            % {"filename": filename, "size_mb": size_mb, "max_size_mb": max_single_size},
        }

    return {"accepted": True}
