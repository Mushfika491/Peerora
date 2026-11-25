"""CSV exports for administrators.

Cells that start with = + - @ (or a tab/carriage return) are prefixed with an
apostrophe so spreadsheet programs do not run them as formulas (CSV injection).
"""

import csv
import io
from collections.abc import Iterable, Iterator
from typing import Any

MAX_EXPORT_ROWS = 10_000
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def csv_rows(header: list[str], rows: Iterable[list[Any]]) -> Iterator[str]:
    """Yield the CSV text line by line (streamed, so large exports use little memory)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    yield buffer.getvalue()
    for row in rows:
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow([safe_cell(value) for value in row])
        yield buffer.getvalue()
