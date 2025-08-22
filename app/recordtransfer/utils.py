import functools
import os
from collections import defaultdict
from pathlib import Path
from typing import List
from zipfile import ZipFile

from django.conf import settings
from django.http import HttpRequest
from django.utils.html import strip_tags
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


@functools.lru_cache(maxsize=1)
def is_deployed_environment() -> bool:
    """Detect if the app is running in a deployed production environment.

    Returns True if ALLOWED_HOSTS contains any non-localhost/non-127.0.0.1 hosts,
    indicating this is a deployed production environment.
    """
    allowed_hosts = settings.ALLOWED_HOSTS

    # If ALLOWED_HOSTS is ['*'], consider it production
    if "*" in allowed_hosts:
        return True

    # Check if any host is not localhost/127.0.0.1
    for host in allowed_hosts:
        host = host.strip().lower()
        if host not in ["localhost", "127.0.0.1", ""]:
            return True

    return False


def get_client_ip_address(request: HttpRequest) -> str:
    """Get the client's IP address from the request."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip
