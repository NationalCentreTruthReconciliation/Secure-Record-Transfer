from zipfile import ZipFile
import logging
import os

from recordtransfer.exceptions import FolderNotFoundError

from django.utils.html import strip_tags


LOGGER = logging.getLogger(__name__)

def zip_directory(directory: str, zipf: ZipFile):
    ''' Zip a directory structure into a zip file.

    Args:
        directory (str): The folder to zip
        zipf (ZipFile): A zipfile.ZipFile handle
    '''
    if not os.path.isdir(directory):
        raise FolderNotFoundError(f'Directory {directory} does not exist')
    if not zipf:
        raise ValueError('ZipFile does not exist')

    relroot = os.path.abspath(os.path.join(directory, os.pardir))
    for root, _, files in os.walk(directory):
        # add directory (needed for empty dirs)
        zipf.write(root, os.path.relpath(root, relroot))
        for file_ in files:
            filename = os.path.join(root, file_)
            if os.path.isfile(filename): # regular files only
                arcname = os.path.join(os.path.relpath(root, relroot), file_)
                zipf.write(filename, arcname)


def snake_to_camel_case(string: str):
    string_split = string.split('_')
    return string_split[0] + ''.join([x.capitalize() for x in string_split[1:]])


def html_to_text(html: str):
    no_tags_split = strip_tags(html).split('\n')
    plain_text_split = filter(None, map(str.strip, no_tags_split))
    return '\n'.join(plain_text_split)


def get_human_readable_size(size_bytes: int, base=1024, precision=2):
    ''' Convert bytes into a human-readable size.

    Args:
        size_bytes: The number of bytes to convert
        base: Either of 1024 or 1000. 1024 for sizes like MiB, 1000 for sizes
            like MB
        precision: The number of decimals on the returned size

    Returns:
        (str): The bytes converted to a human readable size
    '''
    if base not in (1000, 1024):
        raise ValueError('base may only be 1000 or 1024')
    if size_bytes < 0:
        raise ValueError('size_bytes cannot be negative')

    suffixes = {
        1000: ('B', 'KB',  'MB',  'GB',  'TB',  'PB',  'EB',  'ZB',  'YB'),
        1024: ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    }

    if size_bytes < base:
        return '%d %s' % (size_bytes, suffixes[base][0])

    suffix = suffixes[base][0]
    for suffix in suffixes[base]:
        if round(size_bytes) < base:
            break
        size_bytes /= float(base)

    return "%.*f %s" % (precision, size_bytes, suffix)


def get_human_readable_file_count(file_names: list, accepted_file_groups: dict, logger=None):
    ''' Count the number of files falling into the ACCEPTED_FILE_FORMATS groups, and report (in
    English) the number of files in each group.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of
            lowercase file extensions without periods.
        logger (Logger): A logging instance for any messages.

    Returns:
        (str): A string reporting the number of files in each group.
    '''
    logger = logger or LOGGER

    counted_types = count_file_types(file_names, accepted_file_groups, logger=logger)
    if not counted_types:
        return 'No file types could be identified'

    statement = []
    for group, num in counted_types.items():
        if num < 1:
            continue
        statement.append(f'1 {group} file' if num == 1 else f'{num} {group} files')

    if not statement:
        return 'No file types could be identified'

    string_statement = ''
    if len(statement) == 1:
        string_statement = statement[0]
    elif len(statement) == 2:
        string_statement = f'{statement[0]} and {statement[1]}'
    else:
        all_except_last = statement[0:-1]
        comma_joined_string = ', '.join(all_except_last)
        string_statement = f'{comma_joined_string}, and {statement[-1]}'
    return string_statement


def count_file_types(file_names: list, accepted_file_groups: dict, logger=None):
    ''' Tabulate how many files fall into the file groups specified in the ACCEPTED_FILE_FORMATS
    dictionary.

    If a file's extension does not match any of the accepted file extensions, it is ignored. For
    that reason, it is important to ensure that the files are accepted before trying to count them.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of
            lowercase file extensions without periods.
        logger (Logger): A logging instance.

    Returns:
        (dict): A dictionary mapping from group name to number of files in that group.
    '''
    logger = logger or LOGGER

    counted_extensions = {}

    # Tabulate number of times each extension each appears
    for name in file_names:
        split_name = name.split('.')
        if len(split_name) == 1:
            logger.warning(msg=('Could not identify file type for file name: {0}'.format(name)))
        else:
            extension_name = split_name[-1].lower()
            if extension_name not in counted_extensions:
                counted_extensions[extension_name] = 1
            else:
                counted_extensions[extension_name] += 1

    counted_extensions_per_group = {}
    if not counted_extensions:
        return counted_extensions_per_group

    # Tabulate number of files in each file type group
    del_keys = []
    for file_group_name, extensions_for_file_group in accepted_file_groups.items():
        for counted_extension_name, num_counted in counted_extensions.items():
            if counted_extension_name in extensions_for_file_group:
                if file_group_name not in counted_extensions_per_group:
                    counted_extensions_per_group[file_group_name] = num_counted
                else:
                    counted_extensions_per_group[file_group_name] += num_counted
                del_keys.append(counted_extension_name)
        # Remove counted extensions
        for key in del_keys:
            del counted_extensions[key]
        del_keys.clear()

    return counted_extensions_per_group
