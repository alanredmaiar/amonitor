from datetime import datetime, timezone
from pathlib import Path


def to_timestamp(value: str | int) -> int:
    """Converts a string in the format 'YYYY-MM-DDTHH:MM:SS.sssZ' to a timestamp."""
    if isinstance(value, int):
        return value
    try:
        parts = value.split('.')
        if len(parts) > 1:
            adjusted_microseconds = parts[1][:6] + 'Z'
            value = parts[0] + '.' + adjusted_microseconds
        date_time_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        date_time_obj = date_time_obj.replace(tzinfo=timezone.utc)
        return int(date_time_obj.timestamp())
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {value}")


def safe_path(path: str | Path) -> Path:
    """Returns a safe path by incrementally numbering the filename if it already exists."""
    path = Path(path)
    original_path = path
    counter = 1
    parent_dir = path.parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True)
    while path.exists():
        path = original_path.parent / f"{original_path.stem}_{counter}{original_path.suffix}"
        counter += 1
    return path
