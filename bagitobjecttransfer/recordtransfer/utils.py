import os
from pathlib import Path
from typing import Union
from zipfile import ZipFile

from django.conf import settings
from django.utils.html import strip_tags

from recordtransfer.exceptions import FolderNotFoundError


def zip_directory(directory: str, zipf: ZipFile) -> None:
    """Zip a directory structure into a zip file.

    Args:
        directory: The folder to zip
        zipf: A zipfile.ZipFile handle (i.e., an open zip file that can be written to)
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
    """Convert a string from snake_case to camelCase.

    Args:
        string: The snake case string.

    Returns:
        The same string in camel case.
    """
    string_split = string.split("_")
    return string_split[0] + "".join([x.capitalize() for x in string_split[1:]])


def html_to_text(html: str) -> str:
    """Strip HTML from a string and return only the text content.

    Args:
        html: A string that may contain HTML tags.

    Returns:
        The string without HTML tags.
    """
    no_tags_split = strip_tags(html).split("\n")
    plain_text_split = filter(None, map(str.strip, no_tags_split))
    return "\n".join(plain_text_split)


def get_human_readable_size(
    size_bytes: Union[int, float],
    base: int = 1024,
    precision: int = 2,
) -> str:
    """Convert bytes into a human-readable size.

    Args:
        size_bytes: The number of bytes to convert
        base: Either 1024 or 1000. 1024 for sizes like MiB, 1000 for sizes like MB
        precision: The number of decimals on the returned size

    Returns:
        The bytes converted to a human readable size.
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
        return f"{size_bytes:.0f} {suffixes[base][0]}"

    size_float = float(size_bytes)
    base_float = float(base)

    i = 0
    while size_float >= base_float and i < len(suffixes[base]) - 1:
        size_float /= float(base)
        i += 1

    suffix = suffixes[base][i]

    return f"{size_float:.{precision}f} {suffix}"


def get_human_readable_file_count(file_names: list[str]) -> str:
    """Count the number of files falling into the ACCEPTED_FILE_FORMATS groups, and report (in
    English) the number of files in each group.

    Args:
        file_names: A list of file paths or names with extension intact

    Returns:
        A string reporting the number of files in each group.
    """
    counted_types = count_file_types(file_names)
    if not counted_types:
        return "No file types could be identified"

    statement = []
    for group, num in counted_types.items():
        if num < 1 or group is None:
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


def count_file_types(file_names: list[str]) -> dict[Union[str, None], int]:
    """Tabulate how many files fall into the file groups specified in the ACCEPTED_FILE_FORMATS
    dictionary.

    If a file's extension does not match any of the accepted file extensions, it is added to the
    None group.

    Args:
        file_names: A list of file paths or names with extension intact

    Returns:
        A dictionary mapping from group name to number of files in that group.
    """
    group_names = {
        extension: group_name
        for group_name, extension_set in settings.ACCEPTED_FILE_FORMATS.items()
        for extension in extension_set
    }

    files_per_group = {}

    for file_name in file_names:
        suffix = Path(file_name).suffix.lower().lstrip(".")
        group = group_names.get(suffix)

        if group not in files_per_group:
            files_per_group[group] = 0

        files_per_group[group] += 1

    return files_per_group
