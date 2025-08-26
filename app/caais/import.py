import logging

from caais.csvfile import Columns
from caais.db import MULTI_VALUE_SEPARATOR
from caais.models import Identifier, Metadata

LOGGER = logging.getLogger(__name__)


def is_empty_cell(cell: str) -> bool:
    """Determine if a cell should be considered empty or not."""
    return not cell or cell.lower() not in ("null", "nan")


def validate_fieldnames(row: dict, columns: Columns = Columns.CAAIS_1_0) -> None:
    """Compare the columns of a CSV row with the expected columns for the given CSV type.

    Args:
        row: A CSV row, as a dictionary.
        columns: The type of CSV columns.
    """
    row_cols = set(row.keys())
    expected_cols = set(columns.fieldnames)

    extra_cols = row_cols - expected_cols
    missing_cols = expected_cols - row_cols

    if extra_cols:
        row_cols_list = list(row.keys())
        raise ValueError(
            "Extra unexpected columns in CSV: {cols}".format(
                cols=", ".join(sorted(extra_cols, key=lambda c: row_cols_list.index(c)))
            )
        )
    if missing_cols:
        raise ValueError(
            "Missing columns from CSV: {cols}".format(
                cols=", ".join(sorted(missing_cols, key=lambda c: columns.fieldnames.index(c)))
            )
        )


def split_cells(row: dict, *cols) -> tuple[list[str], ...]:
    """Split cells from one or more columns by the MULTI_VALUE_SEPARATOR.

    If multiple cols are passed, the number of elements in each col after splitting is compared. If
    there is a mismatch in the number of elements between any column, a ValueError is raised.
    """
    el_count = -1

    split = []

    for i, col in enumerate(cols):
        col_split = list(map(str.strip, row[col].split(MULTI_VALUE_SEPARATOR)))
        curr_el_count = len(col_split)

        # Compare all future counts against this first count
        if el_count == -1:
            el_count = curr_el_count

        elif el_count != curr_el_count:
            # We've only enumerated up to the current column, so we can only use previous columns
            others = ", ".join(f"'{c}'" for c in cols[0:i])
            raise ValueError(
                f"The column '{col}' has a different number of elements compared to these other "
                f"columns: {others}. These columns are all required to have the same number of "
                f"elements, separated by a {MULTI_VALUE_SEPARATOR} character"
            )

        clean_col_split = [value if not is_empty_cell(value) else None for value in col_split]

        split.append(clean_col_split)

    return tuple(split)


def create_metadata(row: dict, columns: Columns, allow_new_terms: bool) -> None:
    """Create the parent Metadata object that all other data that connects to it."""
    metadata = Metadata()

    metadata.save()

    create_identifiers(metadata, row, columns)


def create_identifiers(metadata: Metadata, row: dict, columns: Columns) -> None:
    """Convert CSV data to Identifier objects."""
    if columns.is_atom:
        _create_identifiers_atom(metadata, row, columns)
    else:
        _create_identifiers_caais(metadata, row, columns)


def _create_identifiers_atom(metadata: Metadata, row: dict, columns: Columns) -> None:
    # The alternativeIdentifier columns were added in 2.6
    if columns in (Columns.ATOM_2_1, Columns.ATOM_2_2, Columns.ATOM_2_3):
        return

    if columns != columns.ATOM_2_6:
        raise ValueError(f"Only {columns.ATOM_2_6!r} is supported.")

    data = split_cells(
        row,
        "alternativeIdentifierTypes",
        "alternativeIdentifiers",
        "alternativeIdentifierNotes",
    )
    for id_type, id_value, id_note in zip(*data, strict=True):
        if id_type == "Accession Identifier":
            LOGGER.warning("Skipping adding reserved 'Accession Identifier' alternativeIdentifier")
            continue

        Identifier.objects.create(
            metadata=metadata,
            identifier_type=id_type,
            identifier_value=id_value,
            identifier_note=id_note,
        )

    if not is_empty_cell(row["accessionNumber"]):
        Identifier.objects.create(
            metadata=metadata,
            identifier_type="Accession Identifier",
            identifier_value=row["accessionNumber"].strip(),
        )


def _create_identifiers_caais(metadata: Metadata, row: dict, columns: Columns) -> None:
    if columns != Columns.CAAIS_1_0:
        raise ValueError(f"Only {columns.CAAIS_1_0!r} is supported")

    data = split_cells(
        row,
        "identifierTypes",
        "identifierValues",
        "identifierNotes",
    )

    accession_id_found = False

    for id_type, id_value, id_note in zip(*data, strict=True):
        if id_type == "Accession Identifier":
            if accession_id_found:
                LOGGER.warning("Skipping adding duplicate 'Accession Identifier'")
                continue
            accession_id_found = True

        Identifier.objects.create(
            metadata=metadata,
            identifier_type=id_type,
            identifier_value=id_value,
            identifier_note=id_note,
        )
