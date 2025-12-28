# Copyright 2025 Christophe Roeder. All rights reserved.

"""HL7 datetime parsing utilities."""

from datetime import datetime
from typing import Optional


def parse_hl7_time(s: str) -> Optional[datetime]:
    """
    Parse HL7 datetime format (YYYYMMDDHHMMSS, YYYYMMDD, etc.).

    Supported formats:
    - YYYYMMDDHHMMSS (full datetime)
    - YYYYMMDDHHMM
    - YYYYMMDDHH
    - YYYYMMDD (date only)
    - YYYYMM
    - YYYY

    Timezone suffixes (Z, +/-HHMM) are stripped and ignored.

    Args:
        s: HL7 datetime string

    Returns:
        Parsed datetime, or None if empty or invalid
    """
    if not s:
        return None

    # Remove timezone suffix if present
    s = s.rstrip("Z")

    # Remove +/- timezone offset
    for sep in ("+", "-"):
        if sep in s[1:]:  # Don't match leading minus
            idx = s.rfind(sep)
            if idx > 0:
                s = s[:idx]
                break

    # Try parsing with various formats (longest to shortest)
    formats = [
        ("%Y%m%d%H%M%S", 14),  # Full datetime
        ("%Y%m%d%H%M", 12),  # No seconds
        ("%Y%m%d%H", 10),  # Hour only
        ("%Y%m%d", 8),  # Date only
        ("%Y%m", 6),  # Year and month
        ("%Y", 4),  # Year only
    ]

    for fmt, length in formats:
        if len(s) >= length:
            try:
                return datetime.strptime(s[:length], fmt)
            except ValueError:
                continue

    return None
