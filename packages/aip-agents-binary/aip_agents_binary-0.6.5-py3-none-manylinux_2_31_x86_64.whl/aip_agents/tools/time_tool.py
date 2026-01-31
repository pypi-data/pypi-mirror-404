"""Tool to get the current time.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import re
from datetime import datetime, timedelta, timezone, tzinfo

from dateutil import tz
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

FORMAT_STRING = "%m/%d/%y %H:%M:%S"
DEFAULT_TIMEZONE = "UTC+7"


class TimeToolInput(BaseModel):
    """Input schema for the TimeTool."""

    datetime_format: str = Field(
        default=FORMAT_STRING,
        description="""
        Optional datetime format string. Default: '%m/%d/%y %H:%M:%S'

        Common format codes:
        %Y: Year with century (2024)
        %m: Month as number (01-12)
        %d: Day of month (01-31)
        %A: Full weekday name (Wednesday)
        %a: Short weekday name (Wed)
        %H: Hour (00-23)
        %M: Minute (00-59)
        %S: Second (00-59)
        %Z: Timezone name
        %j: Day of year (001-366)
        %W: Week number (00-53, Monday first)
        %U: Week number (00-53, Sunday first)
        %c: Locale's date and time
        %x: Locale's date
        %X: Locale's time
        """,
    )
    timezone: str | None = Field(
        default=DEFAULT_TIMEZONE,
        description="""
        Optional timezone identifier. Supports IANA names (e.g., 'Asia/Jakarta')
        or offsets (e.g., 'UTC+7', 'UTC-04:30'). Default: 'UTC+7' (Asia/Jakarta).
        Highly recommended to be filled when getting the current time to ensure
        the time is in the correct timezone.
        """,
    )


def _parse_timezone(timezone_value: str | None) -> tzinfo | None:
    """Return a tzinfo instance for a given timezone string.

    Args:
        timezone_value: Timezone string (e.g., "UTC+7", "UTC-5:30") or None.

    Returns:
        tzinfo instance or None if invalid/None input.
    """
    if timezone_value is None:
        return None

    tz_string = timezone_value.strip()
    if not tz_string:
        return None

    offset_match = re.fullmatch(r"UTC([+-])(\d{1,2})(?::?(\d{2}))?$", tz_string.upper())
    if offset_match:
        sign, hours_str, minutes_str = offset_match.groups()
        hours = int(hours_str)
        minutes = int(minutes_str) if minutes_str else 0
        MAX_HOURS_OFFSET = 12
        MINUTES_OFFSETS = [0, 30, 45]
        if hours > MAX_HOURS_OFFSET or minutes not in MINUTES_OFFSETS:
            raise ValueError(f"Invalid timezone offset: {timezone_value}")
        delta = timedelta(hours=hours, minutes=minutes)
        if sign == "-":
            delta = -delta
        return timezone(delta)

    tzinfo = tz.gettz(tz_string)
    if tzinfo is not None:
        return tzinfo

    raise ValueError(f"Unknown timezone: {timezone_value}")


class TimeTool(BaseTool):
    """Tool to get the current time."""

    name: str = "time_tool"
    description: str = """
    Useful for getting the current time in a specified format and timezone.
    Default format: '%m/%d/%y %H:%M:%S' (e.g., '05/15/24 17:30:00')

    Supports timezone specification to get the current time in any timezone.
    It is highly recommended to specify a timezone to ensure accurate results.
    """
    args_schema: type[BaseModel] = TimeToolInput

    def _run(self, datetime_format: str = FORMAT_STRING, timezone: str | None = DEFAULT_TIMEZONE) -> str:
        """Get current time formatted according to the specified format and timezone.

        Args:
            datetime_format: Format string for datetime (default: ISO format).
            timezone: Timezone string (default: UTC).

        Returns:
            Formatted datetime string.
        """
        tzinfo = _parse_timezone(timezone)
        current_time = datetime.now(tz=tzinfo)
        return current_time.strftime(datetime_format)
