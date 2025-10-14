# /// scripts
# requires-python = ">=3.11"
# dependencies = [
#   "polib",
# ]
# ///
"""Merge translations from one PO file to another.

Copies translations from the source file to the target file for matching msgids.


Call it like:

    uv run scripts/merge_translations.py django.po new-translations.po

"""

import argparse
import logging

import polib

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_arg_parser() -> argparse.ArgumentParser:
    """Create an argument parser for this script."""
    parser = argparse.ArgumentParser(
        description="Update target .po file with translations from the source .po file."
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file to write updated .po file to. Defaults to overwriting target path",
    )
    parser.add_argument("source", help="Source file containing translations to copy")
    parser.add_argument("target", help="Target file to update with translations from source")
    return parser


def load_source_translations(source_po: polib.POFile) -> dict:
    """Load translations from source PO file."""
    source_translations = {}

    for entry in source_po:
        # Only include entries that have translations
        if not entry.msgstr:
            continue

        # Create a key that handles both simple and context-based messages
        key = (entry.msgctxt or "", entry.msgid)
        source_translations[key] = entry.msgstr

        # Also handle plural forms
        if entry.msgid_plural:
            plural_key = (entry.msgctxt or "", entry.msgid, entry.msgid_plural)
            source_translations[plural_key] = entry.msgstr_plural

    return source_translations


def update_target_translations(target_po: polib.POFile, source_translations: dict) -> int:
    """Update translations for target in-place.

    Returns:
        The number of translations updated.
    """
    updated_count = 0

    for entry in target_po:
        key = (entry.msgctxt or "", entry.msgid)

        if entry.msgid_plural:
            plural_key = (entry.msgctxt or "", entry.msgid, entry.msgid_plural)
            if (
                plural_key in source_translations
                and entry.msgstr_plural != source_translations[plural_key]
            ):
                entry.msgstr_plural = source_translations[plural_key]
                if "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")
                updated_count += 1

        elif key in source_translations and entry.msgstr != source_translations[key]:
            entry.msgstr = source_translations[key]
            if "fuzzy" in entry.flags:
                entry.flags.remove("fuzzy")
            updated_count += 1

    return updated_count


def merge_po_files(source_path: str, target_path: str, output_path: str | None = None) -> None:
    """Merge translations from source PO file into target PO file.

    Args:
        source_path: Path to the PO file with translations to copy from
        target_path: Path to the PO file to update
        output_path: Optional path to write the merged file (defaults to target_path)
    """
    logging.info("Loading source file: %s", source_path)
    source_po = polib.pofile(source_path)

    logging.info("Loading target file: %s", target_path)
    target_po = polib.pofile(target_path)

    source_translations = load_source_translations(source_po)
    logging.info("Found %d translated entries in source file", len(source_translations))

    updated_count = update_target_translations(target_po, source_translations)

    if updated_count == 0:
        logging.info("Target file is up to date with source translations.")
    elif updated_count == 1:
        logging.info("Updated 1 entry in target file")
    else:
        logging.info("Updated %d entries in target file", updated_count)

    if updated_count > 0:
        # Save the merged file
        output = output_path or target_path
        logging.info("Saving merged file to: %s", output)
        target_po.save(output)


if __name__ == "__main__":
    parser = get_arg_parser()
    parsed = parser.parse_args()

    merge_po_files(parsed.source, parsed.target, parsed.output)
