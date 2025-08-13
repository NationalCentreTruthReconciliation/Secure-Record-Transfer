import contextlib
import logging
import os
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, List, Union
from zipfile import ZipFile

from django.conf import settings
from django.utils.html import strip_tags
from django.utils.translation import gettext, ngettext_lazy, pgettext_lazy
from django.utils.translation import gettext_lazy as _

# This is to avoid a circular import
if TYPE_CHECKING:
    from recordtransfer.models import UploadSession

LOGGER = logging.getLogger(__name__)


def zip_directory(directory: str, zipf: ZipFile) -> None:
    """Zip a directory structure into a zip file.

    Args:
        directory (str): The folder to zip
        zipf (ZipFile): A zipfile.ZipFile handle
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist")
    if not zipf:
        raise ValueError("ZipFile does not exist")

    relroot = os.path.abspath(os.path.join(directory, os.pardir))
    for root, __, files in os.walk(directory):
        # add directory (needed for empty dirs)
        zipf.write(root, os.path.relpath(root, relroot))
        for file_ in files:
            filename = os.path.join(root, file_)
            if os.path.isfile(filename):  # regular files only
                arcname = os.path.join(os.path.relpath(root, relroot), file_)
                zipf.write(filename, arcname)


def snake_to_camel_case(string: str) -> str:
    """Convert a snake_case string to camelCase."""
    string_split = string.split("_")
    return string_split[0] + "".join([x.capitalize() for x in string_split[1:]])


def html_to_text(html: str) -> str:
    """Convert HTML content to plain text by stripping tags and whitespace."""
    no_tags_split = strip_tags(html).split("\n")
    plain_text_split = filter(None, map(str.strip, no_tags_split))
    return "\n".join(plain_text_split)


def get_human_readable_size(size_bytes: float, base: int = 1024, precision: int = 2) -> str:
    """Convert bytes into a human-readable size.

    Args:
        size_bytes: The number of bytes to convert
        base: Either of 1024 or 1000. 1024 for sizes like MiB, 1000 for sizes
            like MB
        precision: The number of decimals on the returned size

    Returns:
        (str): The bytes converted to a human readable size
    """
    if base not in (1000, 1024):
        raise ValueError("base may only be 1000 or 1024")
    if size_bytes < 0:
        raise ValueError("size_bytes cannot be negative")

    suffixes = {
        1000: ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"),
        1024: ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"),
    }

    if size_bytes < base:
        return "%d %s" % (size_bytes, suffixes[base][0])

    suffix_list = suffixes[base]
    idx = 0
    while size_bytes >= base and idx < len(suffix_list) - 1:
        size_bytes /= float(base)
        idx += 1

    return "%.*f %s" % (precision, size_bytes, suffix_list[idx])


def get_human_readable_file_count(file_names: list, accepted_file_groups: dict) -> str:
    """Count the number of files falling into the ACCEPTED_FILE_FORMATS groups, and report the
    number of files in each group.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of
            lowercase file extensions without periods.

    Returns:
        (str): A string reporting the number of files in each group.
    """
    counted_types = count_file_types(file_names, accepted_file_groups)
    if not counted_types:
        return _("No file types could be identified")

    statement = []
    for group, num in counted_types.items():
        if num < 1:
            continue
        statement.append(
            ngettext_lazy(
                "%(count)s %(file_type)s file",
                "%(count)s %(file_type)s files",
                num,
            )
            % {
                "count": num,
                "file_type": group,
            }
        )

    if not statement:
        return _("No file types could be identified")

    if len(statement) == 1:
        return statement[0]

    if len(statement) == 2:
        return pgettext_lazy(
            "file_count_1 and _2 are both counts like: '1 PDF file'",
            "%(file_count_1)s and %(file_count_2)s",
        ) % {
            "file_count_1": statement[0],
            "file_count_2": statement[1],
        }

    return pgettext_lazy(
        "file_count_1 is a list like '1 PDF file, 2 Image files' and file_count_2 is a count like: '5 Video files'",
        "%(file_count_1)s, and %(file_count_2)s",
    ) % {
        "file_count_1": ", ".join(statement[0:-1]),
        "file_count_2": statement[-1],
    }


def count_file_types(file_names: list, accepted_file_groups: dict[str, List[str]]) -> dict:
    """Tabulate how many files fall into the file groups specified in the ACCEPTED_FILE_FORMATS
    dictionary.

    If a file's extension does not match any of the accepted file extensions, it is ignored. For
    that reason, it is important to ensure that the files are accepted before trying to count them.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of
            lowercase file extensions without periods.

    Returns:
        (dict): A dictionary mapping from group name to number of files in that group.
    """
    # Invert dict so it maps from extension -> name instead of name -> extensions
    names_for_extensions = {
        extension: file_type_name
        for file_type_name, file_extension_list in accepted_file_groups.items()
        for extension in file_extension_list
    }

    counts = defaultdict(int)

    for name in file_names:
        parts = name.split(".")

        if len(parts) < 2:
            continue

        extension = parts[-1].lower()

        if extension not in names_for_extensions:
            continue

        name = names_for_extensions[extension]
        counts[name] += 1

    return dict(counts)


def mb_to_bytes(m: int) -> int:
    """Convert MB to bytes.

    Args:
        m (int): Size in MB.

    Returns:
        int: Size in bytes.
    """
    return m * 1000**2


def bytes_to_mb(b: int) -> float:
    """Convert bytes to MB.

    Args:
        b (int): Size in bytes.

    Returns:
        float: Size in MB.
    """
    return b / 1000**2


def accept_file(filename: str, filesize: Union[str, int]) -> dict:
    """Determine if a new file should be accepted. Does not check the file's
    contents, only its name and its size.

    These checks are applied:
    - The file name is safe and not malicious
    - The file name is not empty
    - The file has an extension
    - The file's extension exists in ACCEPTED_FILE_FORMATS
    - The file's size is an integer greater than zero
    - The file's size is less than or equal to the maximum allowed size for one file

    Args:
        filename (str): The name of the file
        filesize (Union[str, int]): A string or integer representing the size of
            the file (in bytes)

    Returns:
        (dict): A dictionary containing an 'accepted' key that contains True if
            the session is valid, or False if not. The dictionary also contains
            an 'error' and 'verboseError' key if 'accepted' is False.
    """
    # Check filename safety first
    filename_check = is_safe_filename(filename)
    if not filename_check["safe"]:
        return {
            "accepted": False,
            "error": filename_check["error"],
            "verboseError": filename_check["error"],
        }

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

    # Check filesize is an integer and non-negative
    try:
        size = int(filesize)
    except (ValueError, TypeError):
        return {
            "accepted": False,
            "error": gettext("File size is invalid."),
            "verboseError": gettext('The file "{0}" has an invalid size ({1})').format(
                filename, filesize
            ),
        }
    if size < 0:
        return {
            "accepted": False,
            "error": gettext("File size is invalid."),
            "verboseError": gettext('The file "%(filename)s" has an invalid size (%(size)s)')
            % {"filename": filename, "size": size},
        }
    if size == 0:
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
    size_mb = bytes_to_mb(size)
    if size > max_single_size_bytes:
        return {
            "accepted": False,
            "error": gettext("File is too big (%(size_mb).2fMB). Max filesize: %(max_size)sMB")
            % {"size_mb": size_mb, "max_size": max_single_size},
            "verboseError": gettext(
                'The file "%(filename)s" is too big (%(size_mb).2fMB). Max filesize: %(max_size)sMB'
            )
            % {"filename": filename, "size_mb": size_mb, "max_size": max_single_size},
        }

    # All checks succeeded
    return {"accepted": True}


def accept_session(filename: str, filesize: Union[str, int], session: "UploadSession") -> dict:
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


def is_safe_filename(filename: str) -> dict:
    """Validate that a filename is safe and not malicious.

    Args:
        filename (str): The filename to validate

    Returns:
        dict: A dictionary with 'safe' boolean and optional 'error' message
    """
    validators = [
        _validate_basic_filename,
        _validate_filename_characters,
        _validate_path_traversal,
        _validate_absolute_paths,
        _validate_windows_reserved_names,
        _validate_path_components,
    ]

    for validator in validators:
        result = validator(filename)
        if not result["safe"]:
            return result

    return {"safe": True}


def _validate_basic_filename(filename: str) -> dict:
    """Validate basic filename properties."""
    if not filename or not filename.strip():
        return {
            "safe": False,
            "error": gettext("Filename cannot be empty"),
        }

    if len(filename) > 255:
        return {
            "safe": False,
            "error": gettext("Filename is too long"),
        }

    return {"safe": True}


def _validate_filename_characters(filename: str) -> dict:
    """Validate filename doesn't contain control characters."""
    if any(ord(char) < 32 for char in filename):
        return {
            "safe": False,
            "error": gettext("Filename contains invalid characters"),
        }

    return {"safe": True}


def _validate_path_traversal(filename: str) -> dict:
    """Validate filename doesn't contain path traversal patterns."""
    decoded_filename = filename

    with contextlib.suppress(Exception):
        decoded_filename = urllib.parse.unquote(filename)

    traversal_patterns = [
        "..",
        "/",
        "\\",
        "%2e%2e",
        "%2f",
        "%5c",  # URL encoded
        "%252e",
        "%252f",
        "%255c",  # Double encoded
    ]

    for pattern in traversal_patterns:
        if pattern in decoded_filename.lower() or pattern in filename.lower():
            return {
                "safe": False,
                "error": gettext("Filename contains invalid path characters"),
            }

    return {"safe": True}


def _validate_absolute_paths(filename: str) -> dict:
    """Validate filename doesn't contain absolute path patterns."""
    if filename.startswith("/") or (len(filename) > 2 and filename[1] == ":"):
        return {
            "safe": False,
            "error": gettext("Absolute paths are not allowed"),
        }

    return {"safe": True}


def _validate_windows_reserved_names(filename: str) -> dict:
    """Validate filename doesn't use Windows reserved names."""
    windows_reserved = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    base_name = filename.split(".")[0].upper()
    if base_name in windows_reserved:
        return {
            "safe": False,
            "error": gettext("Filename uses reserved system name"),
        }

    return {"safe": True}


def _validate_path_components(filename: str) -> dict:
    """Validate path components aren't excessively long."""
    path_components = filename.replace("\\", "/").split("/")
    for component in path_components:
        if len(component) > 100:
            return {
                "safe": False,
                "error": gettext("Path component is too long"),
            }

    return {"safe": True}


def get_js_translation_version() -> str:
    """Return the latest modification time of all djangojs.mo files in the locale directory.

    This changes whenever compiled JS translations are updated.
    """
    return str(
        max(
            [
                item.stat().st_mtime
                for locale_dir in settings.LOCALE_PATHS
                for item in Path(locale_dir).rglob("djangojs.mo")
            ]
            or [0]
        )
    )
