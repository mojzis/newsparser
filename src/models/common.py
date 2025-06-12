from datetime import date
from enum import Enum
from typing import TypeAlias

DatePath: TypeAlias = str  # Format: "YYYY/MM/DD"
FileType = Enum("FileType", ["PARQUET", "HTML", "JSON"])


def date_to_path(d: date) -> DatePath:
    """Convert a date to a path format YYYY/MM/DD."""
    return f"{d.year:04d}/{d.month:02d}/{d.day:02d}"


def path_to_date(path: DatePath) -> date:
    """Convert a path format YYYY/MM/DD to a date object."""
    parts = path.split("/")
    if len(parts) != 3:
        raise ValueError(f"Invalid date path format: {path}")

    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid date path format: {path}") from e
