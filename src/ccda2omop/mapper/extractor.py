# Copyright 2025 Christophe Roeder. All rights reserved.

"""XPath-based data extraction from C-CDA XML."""

from datetime import datetime
from typing import Optional

from lxml import etree

from ..ccda.hl7_time import parse_hl7_time
from ..ccda.models import CodedValue, EffectiveTime, Quantity


def extract_string(node: etree._Element, xpath: str) -> str:
    """Extract a string value using XPath."""
    if node is None:
        return ""

    result = node.xpath(xpath)
    if not result:
        return ""

    if isinstance(result[0], etree._Element):
        return result[0].text or ""
    return str(result[0])


def extract_float(node: etree._Element, xpath: str) -> Optional[float]:
    """Extract a float value using XPath."""
    if node is None:
        return None

    result = node.xpath(xpath)
    if not result:
        return None

    try:
        if isinstance(result[0], etree._Element):
            val = result[0].text or result[0].get("value", "")
        else:
            val = str(result[0])
        return float(val) if val else None
    except ValueError:
        return None


def extract_int(node: etree._Element, xpath: str) -> Optional[int]:
    """Extract an integer value using XPath."""
    if node is None:
        return None

    result = node.xpath(xpath)
    if not result:
        return None

    try:
        if isinstance(result[0], etree._Element):
            val = result[0].text or result[0].get("value", "")
        else:
            val = str(result[0])
        return int(val) if val else None
    except ValueError:
        return None


def extract_time(node: etree._Element, xpath: str) -> Optional[datetime]:
    """Extract a datetime value using XPath."""
    if node is None:
        return None

    result = node.xpath(xpath)
    if not result:
        return None

    if isinstance(result[0], etree._Element):
        val = result[0].get("value", "")
    else:
        val = str(result[0])

    return parse_hl7_time(val)


def extract_code(node: etree._Element, xpath: str) -> CodedValue:
    """Extract a coded value using XPath."""
    if node is None:
        return CodedValue()

    result = node.xpath(xpath)
    if not result:
        return CodedValue()

    elem = result[0]
    if not isinstance(elem, etree._Element):
        return CodedValue()

    code = CodedValue(
        code=elem.get("code", ""),
        code_system=elem.get("codeSystem", ""),
        code_system_name=elem.get("codeSystemName", ""),
        display_name=elem.get("displayName", ""),
    )

    ot_elem = elem.find("originalText")
    if ot_elem is not None and ot_elem.text:
        code.original_text = ot_elem.text

    return code


def extract_effective_time(node: etree._Element, xpath: str) -> EffectiveTime:
    """Extract an effective time range using XPath."""
    if node is None:
        return EffectiveTime()

    result = node.xpath(xpath)
    if not result:
        return EffectiveTime()

    elem = result[0]
    if not isinstance(elem, etree._Element):
        return EffectiveTime()

    et = EffectiveTime(value=parse_hl7_time(elem.get("value", "")))

    low_elem = elem.find("low")
    if low_elem is not None:
        et.low = parse_hl7_time(low_elem.get("value", ""))

    high_elem = elem.find("high")
    if high_elem is not None:
        et.high = parse_hl7_time(high_elem.get("value", ""))

    return et


def extract_quantity(node: etree._Element, xpath: str) -> Quantity:
    """Extract a quantity value using XPath."""
    if node is None:
        return Quantity()

    result = node.xpath(xpath)
    if not result:
        return Quantity()

    elem = result[0]
    if not isinstance(elem, etree._Element):
        return Quantity()

    try:
        val = float(elem.get("value", "0"))
    except ValueError:
        val = 0.0

    return Quantity(value=val, unit=elem.get("unit", ""))


def should_include_entry(node: etree._Element) -> bool:
    """
    Check if an entry should be included based on moodCode and statusCode.

    Only includes entries that:
    - Have moodCode="EVN" (actual event) or no moodCode (defaults to EVN)
    - Have statusCode="completed" or "active" or no statusCode
    """
    if node is None:
        return False

    # Check moodCode
    mood_code = node.get("moodCode", "")
    if mood_code and mood_code != "EVN":
        return False

    # Check statusCode
    status_node = node.find("statusCode")
    if status_node is not None:
        status = status_node.get("code", "")
        if status and status not in ("completed", "active"):
            return False

    return True


def xpath_with_fallback(
    node: etree._Element, primary: str, fallback: str
) -> list:
    """
    Execute primary XPath, falling back to secondary if no results.

    Args:
        node: XML element to search
        primary: Primary XPath expression
        fallback: Fallback XPath expression

    Returns:
        XPath result list
    """
    if not primary:
        if fallback:
            return node.xpath(fallback)
        return []

    result = node.xpath(primary)
    if result:
        return result

    if fallback:
        return node.xpath(fallback)

    return []
