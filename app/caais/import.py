from caais.csvfile import Columns


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
