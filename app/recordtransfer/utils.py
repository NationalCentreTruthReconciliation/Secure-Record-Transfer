import logging
import os
from typing import TYPE_CHECKING, Union
from zipfile import ZipFile

from django.conf import settings
from django.utils.html import strip_tags
from django.utils.translation import gettext

from recordtransfer.exceptions import FolderNotFoundError

# This is to avoid a circular import
if TYPE_CHECKING:
    from recordtransfer.models import UploadSession

LOGGER = logging.getLogger("recordtransfer")


def zip_directory(directory: str, zipf: ZipFile) -> None:
    """Zip a directory structure into a zip file.

    Args:
        directory (str): The folder to zip
        zipf (ZipFile): A zipfile.ZipFile handle
    """
    if not os.path.isdir(directory):
        raise FolderNotFoundError(f"Directory {directory} does not exist")
    if not zipf:
        raise ValueError("ZipFile does not exist")

    relroot = os.path.abspath(os.path.join(directory, os.pardir))
    for root, _, files in os.walk(directory):
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
    """Count the number of files falling into the ACCEPTED_FILE_FORMATS groups, and report (in
    English) the number of files in each group.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of
            lowercase file extensions without periods.

    Returns:
        (str): A string reporting the number of files in each group.
    """
    counted_types = count_file_types(file_names, accepted_file_groups)
    if not counted_types:
        return "No file types could be identified"

    statement = []
    for group, num in counted_types.items():
        if num < 1:
            continue
        statement.append(f"1 {group} file" if num == 1 else f"{num} {group} files")

    if not statement:
        return "No file types could be identified"

    string_statement = ""
    if len(statement) == 1:
        string_statement = statement[0]
    elif len(statement) == 2:
        string_statement = f"{statement[0]} and {statement[1]}"
    else:
        all_except_last = statement[0:-1]
        comma_joined_string = ", ".join(all_except_last)
        string_statement = f"{comma_joined_string}, and {statement[-1]}"
    return string_statement


def _count_extensions(file_names: list) -> dict:
    """Count file extensions in a list of file names."""
    counted_extensions = {}
    for name in file_names:
        split_name = name.split(".")
        if len(split_name) == 1:
            LOGGER.warning("Could not identify file type for file name: %s", name)
            continue
        extension_name = split_name[-1].lower()
        counted_extensions[extension_name] = counted_extensions.get(extension_name, 0) + 1
    return counted_extensions


def _group_extensions(counted_extensions: dict, accepted_file_groups: dict) -> dict:
    """Group counted extensions by accepted file groups."""
    counted_extensions_per_group = {}
    remaining_extensions = counted_extensions.copy()
    for file_group_name, extensions_for_file_group in accepted_file_groups.items():
        for extension in extensions_for_file_group:
            if extension in remaining_extensions:
                counted_extensions_per_group[file_group_name] = (
                    counted_extensions_per_group.get(file_group_name, 0)
                    + remaining_extensions[extension]
                )
                del remaining_extensions[extension]
    return counted_extensions_per_group


def count_file_types(file_names: list, accepted_file_groups: dict) -> dict:
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
    counted_extensions = _count_extensions(file_names)
    if not counted_extensions:
        return {}
    return _group_extensions(counted_extensions, accepted_file_groups)


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
    # Check extension exists
    name_split = filename.split(".")
    if len(name_split) == 1:
        return {
            "accepted": False,
            "error": gettext("File is missing an extension."),
            "verboseError": gettext('The file "{0}" does not have a file extension').format(
                filename
            ),
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
            "error": gettext('Files with "{0}" extension are not allowed.').format(extension),
            "verboseError": gettext('The file "{0}" has an invalid extension (.{1})').format(
                filename, extension
            ),
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
            "verboseError": gettext('The file "{0}" has an invalid size ({1})').format(
                filename, size
            ),
        }
    if size == 0:
        return {
            "accepted": False,
            "error": gettext("File is empty."),
            "verboseError": gettext('The file "{0}" is empty').format(filename),
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
            "error": gettext("File is too big ({0:.2f}MB). Max filesize: {1}MB").format(
                size_mb, max_single_size
            ),
            "verboseError": gettext(
                'The file "{0}" is too big ({1:.2f}MB). Max filesize: {2}MB'
            ).format(filename, size_mb, max_single_size),
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
                'The file "{0}" would push the total file count past the '
                "maximum number of files ({1})"
            ).format(filename, settings.MAX_TOTAL_UPLOAD_SIZE_MB),
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
            "error": gettext("Maximum total upload size ({0} MB) exceeded").format(max_size),
            "verboseError": gettext(
                'The file "{0}" would push the total transfer size past the {1}MB max'
            ).format(filename, max_size),
        }

    # Check that a file with this name has not already been uploaded
    filename_list = [f.name for f in session.get_temporary_uploads()]
    if filename in filename_list:
        return {
            "accepted": False,
            "error": gettext("A file with the same name has already been uploaded."),
            "verboseError": gettext('A file with the name "{0}" has already been uploaded').format(
                filename
            ),
        }

    # All checks succeded
    return {"accepted": True}
