"""Custom config parsers."""

import re


class AcceptedFileTypes(object):
    """Parses a list of file types.

    A list of file types can be specified like this:

    ::

        Archive:zip,7z|Document:doc,docx|Photo:jpg,jpeg,png,tiff


    Which gets parsed into structured data, like this:

    ::

        Archive:
          - zip
          - 7z
        Document:
          - doc
          - docx
        Photo:
          - jpeg
          - jpg
          - png
          - tiff

    """

    FILE_GROUP = re.compile(
        r"^(?P<name>[a-zA-Z0-9\-_][a-zA-Z0-9\-_\s]+)\s*\:\s*(?P<extensions>[\.a-zA-Z0-9,]+)$"
    )
    FILE_EXTENSION = re.compile(r"^\.?(?P<extension>[a-zA-Z0-9]+)$")

    def __call__(self, value: str) -> dict[str, set]:
        """Convert the raw string value into a dictionary.

        The output dictionary will be a list of file groups, and the file types that are accepted
        within that group.

        Args:
            value: The raw string value

        Returns:
            A dictionary mapping from a file type to a set of file suffixes that are considered to
            be of that type
        """
        if not value:
            raise ValueError("accepted file types cannot be empty")

        accepted_types = {}

        all_extensions = set()

        for group in [group.strip() for group in value.split("|")]:
            match_obj = AcceptedFileTypes.FILE_GROUP.match(group)

            if not match_obj:
                raise ValueError(
                    f"the file group '{group}' does not match the format Name:EXT,EXT,EXT"
                )

            name = match_obj.group("name").strip()

            raw_extensions = match_obj.group("extensions")

            if name not in accepted_types:
                accepted_types[name] = set()

            for raw_extension in raw_extensions.split(","):
                ext_match = AcceptedFileTypes.FILE_EXTENSION.match(raw_extension)

                if not ext_match:
                    raise ValueError(
                        f"the extension '{raw_extension}' in the '{name}' file group does not "
                        "look like a file extension - it must only contain letters and numbers, "
                        "and may start with a period"
                    )

                extension = ext_match.group("extension").lower()

                if extension in all_extensions and extension not in accepted_types[name]:
                    raise ValueError(
                        f"the extension '{extension}' was found in multiple file groups - this is "
                        "not allowed"
                    )

                all_extensions.add(extension)
                accepted_types[name].add(extension)

        return accepted_types
