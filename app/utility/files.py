"""Utility functions concerning file manipulation and file counting."""

import os
from collections import defaultdict
from typing import List
from zipfile import ZipFile

from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy, pgettext_lazy


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


def get_human_readable_file_count(file_names: list, accepted_file_groups: dict) -> str:
    """Count the number of files falling into the accepted file groups, and report the number of
    files in each group.

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
