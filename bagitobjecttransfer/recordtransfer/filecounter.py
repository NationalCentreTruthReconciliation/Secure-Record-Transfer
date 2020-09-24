import logging


LOGGER = logging.getLogger(__name__)


def get_human_readable_file_count(file_names: list, accepted_file_groups: dict):
    ''' Count the number of files falling into the ACCEPTED_FILE_FORMATS groups, and report (in
    English) the number of files in each group.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of \
        lowercase file extensions without periods.

    Returns:
        (str): A string reporting the number of files in each group
    '''
    counted_types = count_file_types(file_names, accepted_file_groups)
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


def count_file_types(file_names: list, accepted_file_groups: dict):
    ''' Tabulate how many files fall into the file groups specified in the ACCEPTED_FILE_FORMATS \
    dictionary.

    If a file's extension does not match any of the accepted file extensions, it is ignored. For \
    that reason, it is important to ensure that the files are accepted before trying to count them.

    Args:
        file_names (list): A list of file paths or names with extension intact
        accepted_file_groups (dict): A dictionary of file group names mapping to a list of \
        lowercase file extensions without periods.

    Returns:
        (dict): A dictionary mapping from group name to number of files in that group. For example:
            {'Document': 3, 'Video': 12}
    '''
    counted_extensions = {}

    # Tabulate number of times each extension each appears
    for name in file_names:
        split_name = name.split('.')
        if len(split_name) == 1:
            LOGGER.warning(msg=('Could not identify file type for file name: %s' % name))
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
