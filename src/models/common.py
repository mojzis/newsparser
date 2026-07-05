from datetime import date
from enum import Enum

type DatePath = str  # Format: "YYYY/MM/DD"
FileType = Enum("FileType", ["PARQUET", "HTML", "JSON"])


def date_to_path(d: date) -> DatePath:
    """Convert a date to a path format YYYY/MM/DD."""
    return f"{d.year:04d}/{d.month:02d}/{d.day:02d}"


def path_to_date(path: DatePath) -> date:
    """Convert a path format YYYY/MM/DD to a date object."""
    parts = path.split("/")
    if len(parts) != 3:
        raise ValueError(f"Invalid date path format: {path}")

    y, m, d = parts
    if not (len(y) == 4 and len(m) == 2 and len(d) == 2):
        raise ValueError(f"Invalid date path format: {path}")

    try:
        return date(int(y), int(m), int(d))
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid date path format: {path}") from e
