from caais.csvfile import Columns
from caais.db import MULTI_VALUE_SEPARATOR


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


def split_cell(row: dict, *cols) -> tuple[list[str]]:
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

        clean_col_split = [
            value if value and value.lower() != "null" else None for value in col_split
        ]

        split.append(clean_col_split)

    return tuple(split)
