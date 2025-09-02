"""Utility functions for manipulating binary numbers."""


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
