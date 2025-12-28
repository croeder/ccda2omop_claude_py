# Copyright 2025 Christophe Roeder. All rights reserved.

"""Transform functions for mapping field values."""

from datetime import datetime
from typing import Any, Callable, Optional

from lxml import etree

from .rules import FieldMapping


def transform_none(value: Any, **kwargs) -> Any:
    """No-op transform, returns value as-is."""
    return value


def transform_string(value: Any, **kwargs) -> str:
    """Convert value to string."""
    if value is None:
        return ""
    return str(value)


def transform_int(value: Any, **kwargs) -> Optional[int]:
    """Convert value to integer."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def transform_float(value: Any, **kwargs) -> Optional[float]:
    """Convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def transform_date(value: Any, **kwargs) -> Optional[datetime]:
    """Convert value to date (datetime with time at midnight)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    return None


def transform_time_ptr(value: Any, **kwargs) -> Optional[datetime]:
    """Return datetime value as-is."""
    if isinstance(value, datetime):
        return value
    return None


def format_source_value(code: str, display_name: str) -> str:
    """
    Format a source value from code and display name.

    Returns "code: display_name" if both present, otherwise just the non-empty one.
    """
    if code and display_name:
        return f"{code}: {display_name}"
    return display_name or code or ""


# Registry of transform functions by name
TRANSFORMS: dict[str, Callable] = {
    "none": transform_none,
    "string": transform_string,
    "int": transform_int,
    "float": transform_float,
    "date": transform_date,
    "time_ptr": transform_time_ptr,
    # Vocab transforms are handled specially in rule_engine
    "vocab": transform_none,
    "unit": transform_none,
    "route": transform_none,
    "value_vocab": transform_none,
    "format_source": transform_none,
}


def get_transform(name: str) -> Callable:
    """Get a transform function by name."""
    return TRANSFORMS.get(name, transform_none)
