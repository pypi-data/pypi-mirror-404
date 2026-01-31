"""Tool to get date ranges for common time periods.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import json
import re
from collections.abc import Callable
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

FORMAT_STRING = "%m/%d/%y %H:%M:%S"

MIN_DAYS_FOR_WEEK_SPLIT = 6  # Minimum days difference for week split (7 days inclusive = 6 days difference)
MONTH_NAME_ABBR_THRESHOLD = 3  # len > 3 implies full month name, else try abbreviated form
SUPPORTED_DATE_RANGES = [
    "last_week",
    "this_week",
    "last_month",
    "this_month",
    "yesterday",
    "today",
    "last_7_days",
    "last_30_days",
    "this_quarter",
    "last_quarter",
    "this_year",
    "last_year",
    "[N]_days_ago",
    "[N]_weeks_ago",
    "[N]_months_ago",
    "YYYY-MM-DD to YYYY-MM-DD",
]


class DateRangeToolInput(BaseModel):
    """Input schema for the DateRangeTool."""

    date_range: str = Field(
        ...,
        description="""
        Date range identifier. Supported values:
        - Relative periods: 'last_week', 'this_week', 'last_month', 'this_month'
        - Relative days: 'yesterday', 'today', 'last_7_days', 'last_30_days'
        - Custom range: 'N_days_ago', 'N_weeks_ago', 'N_months_ago' (replace N with number)
        - Quarter: 'this_quarter', 'last_quarter'
        - Year: 'this_year', 'last_year'
        - Natural forms: 'January 2025', 'January-March 2025', 'Q1 2025'
        - Explicit date range: 'YYYY-MM-DD to YYYY-MM-DD' (e.g., '2025-08-01 to 2025-08-07')

        Note: For queries like 'first week of August 2025', convert to explicit format: '2025-08-01 to 2025-08-07'
        """,
    )
    format: str = Field(
        default=FORMAT_STRING,
        description="Optional datetime format string. Default: '%m/%d/%y'",
    )
    split_weeks: bool = Field(
        default=False,
        description=(
            "If True and the resulting period spans more than one week, include a 'weeks' array of Sunday–Saturday"
            " splits that fit within the requested period (not recent fixed weeks)."
        ),
    )


class DateRangeTool(BaseTool):
    """Tool to get date ranges for common time periods."""

    name: str = "date_range_tool"
    description: str = """
    Useful for getting date ranges for various time periods.
    Supports relative dates, custom ranges, and standard periods.
    Returns start and end dates for the specified period.
    """
    args_schema: type[BaseModel] = DateRangeToolInput

    def _parse_custom_range(self, date_range: str) -> tuple[datetime, datetime]:
        """Parse custom range patterns like '3_days_ago', '2_weeks_ago', etc.

        Args:
            date_range (str): A string representing the custom date range in the format '{number}_{unit}_ago',
                              where {number} is an integer and {unit} is one of 'days', 'weeks', or 'months'.

        Returns:
            tuple[datetime, datetime]: A tuple containing the start date and end date corresponding to the custom range.
        """
        pattern = r"(\d+)_(days|weeks|months)_ago"
        match = re.match(pattern, date_range)
        start_date = None
        end_date = None
        if not match:
            raise ValueError(f"Invalid custom range format: {date_range}")

        number, unit = int(match.group(1)), match.group(2)
        today = datetime.now()

        if unit == "days":
            start_date = today - timedelta(days=number)
            end_date = today
        elif unit == "weeks":
            start_date = today - timedelta(weeks=number)
            end_date = today
        elif unit == "months":
            start_date = today - relativedelta(months=number)
            end_date = today

        return start_date, end_date

    def _parse_month(self, month_str: str) -> int:
        """Parse month name (full or abbreviated) to month number (1-12).

        Args:
            month_str (int): The month name string to parse.

        Returns:
            int: The month number (1-12).
        """
        fmt = "%B" if len(month_str) > MONTH_NAME_ABBR_THRESHOLD else "%b"
        try:
            return datetime.strptime(month_str, fmt).month
        except ValueError:
            # Fallback to abbreviated format
            return datetime.strptime(month_str, "%b").month

    def _parse_explicit_range(self, dr: str) -> tuple[datetime, datetime] | None:
        """Parse explicit date range: YYYY-MM-DD to YYYY-MM-DD.

        Args:
            dr (str): The date range string to parse.

        Returns:
            tuple[datetime, datetime] | None: A tuple of (start_date, end_date) if matched, otherwise None.
        """
        m_explicit = re.match(r"^(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})$", dr, flags=re.IGNORECASE)
        if m_explicit:
            try:
                start = datetime.strptime(m_explicit.group(1), "%Y-%m-%d")
                end = datetime.strptime(m_explicit.group(2), "%Y-%m-%d")
                if start > end:
                    raise ValueError("Start date must be before or equal to end date")
                return start, end
            except ValueError:
                return None
        return None

    def _parse_quarter_with_year(self, dr: str) -> tuple[datetime, datetime] | None:
        """Parse quarter with year: Q1 2025.

        Args:
            dr (str): The date range string to parse.

        Returns:
            tuple[datetime, datetime] | None: A tuple of (start_date, end_date) if matched, otherwise None.
        """
        m_q = re.match(r"^Q([1-4])\s+(\d{4})$", dr, flags=re.IGNORECASE)
        if m_q:
            q = int(m_q.group(1))
            year = int(m_q.group(2))
            start_month = (q - 1) * 3 + 1
            start = datetime(year, start_month, 1)
            end = start + relativedelta(months=3, days=-1)
            return start, end
        return None

    def _parse_month_range_with_year(self, dr: str) -> tuple[datetime, datetime] | None:
        """Parse month range within a year: January-March 2025.

        Args:
            dr (str): The date range string to parse.

        Returns:
            tuple[datetime, datetime] | None: A tuple of (start_date, end_date) if matched, otherwise None.
        """
        m_range = re.match(r"^([A-Za-z]{3,9})\s*-\s*([A-Za-z]{3,9})\s+(\d{4})$", dr)
        if m_range:
            m1, m2, year_s = m_range.groups()
            year = int(year_s)
            try:
                start_month = self._parse_month(m1)
                end_month = self._parse_month(m2)
                start = datetime(year, start_month, 1)
                end = datetime(year, end_month, 1) + relativedelta(months=1, days=-1)
                return start, end
            except ValueError:
                return None
        return None

    def _parse_single_month_with_year(self, dr: str) -> tuple[datetime, datetime] | None:
        """Parse single month with year: January 2025.

        Args:
            dr (str): The date range string to parse.

        Returns:
            tuple[datetime, datetime] | None: A tuple of (start_date, end_date) if matched, otherwise None.
        """
        m_single = re.match(r"^([A-Za-z]{3,9})\s+(\d{4})$", dr)
        if m_single:
            mname, year_s = m_single.groups()
            year = int(year_s)
            try:
                month = self._parse_month(mname)
                start = datetime(year, month, 1)
                end = start + relativedelta(months=1, days=-1)
                return start, end
            except ValueError:
                return None
        return None

    def _parse_month_or_range(self, date_range: str) -> tuple[datetime, datetime] | None:
        """Parse inputs like 'January 2025', 'Jan 2025', 'January-March 2025', 'Jan-Mar 2025', 'Q1 2025'.

        Also parses explicit date ranges like '2025-08-01 to 2025-08-07'.

        Args:
            date_range (str): The date range string to parse.
                Can be natural month/quarter forms or explicit YYYY-MM-DD format.

        Returns:
            tuple[datetime, datetime] | None: A tuple of (start_date, end_date) if matched, otherwise None.

        Raises:
            ValueError: If start date is after end date (caught internally and returns None).

        Examples:
            >>> self._parse_month_or_range("January 2025")
            (datetime(2025, 1, 1), datetime(2025, 1, 31))
            >>> self._parse_month_or_range("2025-08-01 to 2025-08-07")
            (datetime(2025, 8, 1), datetime(2025, 8, 7))
        """
        dr = date_range.strip()

        # Try each parser in order
        parsers = [
            self._parse_explicit_range,
            self._parse_quarter_with_year,
            self._parse_month_range_with_year,
            self._parse_single_month_with_year,
        ]

        for parser in parsers:
            result = parser(dr)
            if result:
                return result

        return None

    def _get_quarter_dates(self, today: datetime, last_quarter: bool = False) -> tuple[datetime, datetime]:
        """Calculate the start and end dates of the current or last quarter based on the given date.

        Args:
            today (datetime): The reference date to determine the quarter.
            last_quarter (bool, optional): If True, calculate the dates for the last quarter.
                                           If False, calculate the dates for the current quarter.
                                           Defaults to False.

        Returns:
            tuple[datetime, datetime]: A tuple containing the start and end dates of the quarter.
        """
        current_quarter = (today.month - 1) // 3
        if last_quarter:
            if current_quarter == 0:
                start_date = datetime(today.year - 1, 10, 1)
                end_date = datetime(today.year - 1, 12, 31)
            else:
                start_date = datetime(today.year, 3 * (current_quarter - 1) + 1, 1)
                end_date = datetime(today.year, 3 * current_quarter, 1) + relativedelta(months=1, days=-1)
        else:
            start_date = datetime(today.year, 3 * current_quarter + 1, 1)
            end_date = datetime(today.year, 3 * (current_quarter + 1), 1) + relativedelta(months=1, days=-1)
        return start_date, end_date

    def _days_since_most_recent_sunday(self, date: datetime) -> int:
        """Return days since most recent Sunday (0 if today is Sunday).

        Args:
            date (datetime): The reference date.

        Returns:
            int: Days since most recent Sunday (0-6).
        """
        # weekday(): Mon=0, Tue=1, ..., Sun=6
        # We want Sun=0, Mon=1, ..., Sat=6
        return (date.weekday() + 1) % 7

    def _get_standard_period_dates(self, date_range: str, today: datetime) -> tuple[datetime, datetime]:
        """Calculate the start and end dates for a given standard period relative to a specified date.

        Args:
            date_range (str): The standard period to calculate dates for.
                              Supported values are "last_week", "this_week", "last_month", and "this_month".
            today (datetime): The reference date to calculate the period from.

        Returns:
            tuple[datetime, datetime]: A tuple containing the start and end dates of the specified period.
        """
        if date_range == "last_week":
            # Calculate the previous Saturday (end of last week)
            days_since_sunday = self._days_since_most_recent_sunday(today)
            last_saturday = today - timedelta(days=days_since_sunday + 1)

            # Calculate the previous Sunday (start of last week)
            last_sunday = last_saturday - timedelta(days=6)

            return last_sunday, last_saturday

        if date_range == "this_week":
            # Calculate the most recent Sunday (start of this week)
            days_since_sunday = self._days_since_most_recent_sunday(today)
            sunday = today - timedelta(days=days_since_sunday)

            # Calculate the upcoming Saturday (end of this week)
            saturday = sunday + timedelta(days=6)

            return sunday, saturday

        if date_range == "last_month":
            first_day = today.replace(day=1)
            last_month = first_day - timedelta(days=1)
            return last_month.replace(day=1), last_month

        if date_range == "this_month":
            start = today.replace(day=1)
            return start, start + relativedelta(months=1, days=-1)

        raise ValueError(f"Unknown standard period: {date_range}")

    def _week_bounds_for(self, date: datetime) -> tuple[datetime, datetime]:
        """Return the Sunday-to-Saturday week containing the given date.

        - Sunday is the start of week.
        - Saturday is the end of week.

        Args:
            date (datetime): The date to find the week bounds for.

        Returns:
            tuple[datetime, datetime]: A tuple containing the start and end dates of the week.
        """
        days_since_sunday = self._days_since_most_recent_sunday(date)
        sunday = datetime(date.year, date.month, date.day) - timedelta(days=days_since_sunday)
        saturday = sunday + timedelta(days=6)
        return sunday, saturday

    def _build_week_splits(self, start_date: datetime, end_date: datetime, fmt: str) -> list[dict[str, str]]:
        """Build Sunday–Saturday week splits that intersect [start_date, end_date].

        - Includes partial edge weeks if any day of the Sun–Sat week falls within the requested range.
        - Week entries still use full Sunday–Saturday bounds for consistency.
        - Labels weeks consecutively as week_1, week_2, ...

        Args:
            start_date (datetime): Start of requested period.
            end_date (datetime): End of requested period.
            fmt (str): Format string for dates.

        Returns:
            list[dict]: Weekly split entries with start_date, end_date, and human description.
        """
        weeks: list[dict] = []
        # Anchor on the Sunday of the week that contains start_date
        first_week_sunday, _ = self._week_bounds_for(start_date)
        cursor = first_week_sunday
        idx = 1
        while cursor <= end_date:
            full_week_start = cursor
            full_week_end = cursor + timedelta(days=6)
            # Include any week that intersects the requested range
            if not (full_week_end < start_date or full_week_start > end_date):
                desc = f"From {full_week_start.strftime('%B %d, %Y')} to {full_week_end.strftime('%B %d, %Y')}"
                weeks.append(
                    {
                        "period": f"week_{idx}",
                        "start_date": full_week_start.strftime(fmt),
                        "end_date": full_week_end.strftime(fmt),
                        "description": desc,
                    }
                )
                idx += 1
            cursor += timedelta(days=7)
        return weeks

    def _get_relative_day_dates(self, date_range: str, today: datetime) -> tuple[datetime, datetime]:
        """Calculate the start and end dates for a given relative date range.

        Args:
            date_range (str): The relative date range. Supported values are "yesterday", "today",
                              "last_7_days", and "last_30_days".
            today (datetime): The reference date from which the relative date range is calculated.

        Returns:
            tuple[datetime, datetime]: A tuple containing the start and end dates for the specified
                                       relative date range.
        """
        if date_range == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday

        if date_range == "today":
            return today, today

        if date_range == "last_7_days":
            return today - timedelta(days=7), today

        if date_range == "last_30_days":
            return today - timedelta(days=30), today

        raise ValueError(f"Unknown relative day range: {date_range}")

    def _get_year_dates(self, date_range: str, today: datetime) -> tuple[datetime, datetime]:
        """Returns the start and end dates for the specified year range.

        Args:
            date_range (str): The year range to calculate dates for.
                              Accepted values are "this_year" and "last_year".
            today (datetime): The current date to base the year calculation on.

        Returns:
            Tuple[datetime, datetime]: A tuple containing the start and end dates for the specified year range.
        """
        if date_range == "this_year":
            return datetime(today.year, 1, 1), datetime(today.year, 12, 31)

        if date_range == "last_year":
            return datetime(today.year - 1, 1, 1), datetime(today.year - 1, 12, 31)

        raise ValueError(f"Unknown year range: {date_range}")

    def _format_response(
        self,
        start_date: datetime,
        end_date: datetime,
        date_range: str,
        format: str,
        weeks: list[dict] | None = None,
    ) -> str:
        """Format the response as a JSON string with the given date range information.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.
            date_range (str): A string representation of the date range.
            format (str): The format string to use for formatting the dates.
            weeks (list[dict] | None): Optional weekly splits (Sunday–Saturday) for the period. This
                is included when `split_weeks` is True and the overall period spans more than one week.

        Returns:
            str: A JSON string containing the formatted start date, end date, period, and description.
        """
        if weeks:
            payload: dict = {
                "weeks": weeks,
                "period": date_range,
                "description": f"Split into {len(weeks)} weeks with Sunday-to-Saturday bounds",
            }
            return json.dumps(payload)
        payload: dict = {
            "start_date": start_date.strftime(format),
            "end_date": end_date.strftime(format),
            "period": date_range,
            "description": f"From {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
        }
        return json.dumps(payload)

    def _get_result_and_format(
        self,
        date_range: str,
        format: str,
        split_weeks: bool,
        result: tuple[datetime, datetime],
    ) -> str:
        """Helper to format response with optional week splits.

        Args:
            date_range (str): The date range string to process.
            format (str): The format string to use for the output.
            split_weeks (bool): If True and the resulting period spans more than one week,
                also include a 'weeks' array with Sunday-to-Saturday splits for the recent weeks.
            result (tuple[datetime, datetime]): A tuple containing the start and end dates of the date range.

        Returns:
            str: A formatted date range string or an error message if the date range is unsupported or an error occurs.
        """
        start_date, end_date = result
        weeks = None
        # Only build week splits when requested and range spans more than one week
        if split_weeks and (end_date - start_date).days >= MIN_DAYS_FOR_WEEK_SPLIT:
            weeks = self._build_week_splits(start_date, end_date, format)
        return self._format_response(start_date, end_date, date_range, format, weeks=weeks)

    def _run(self, date_range: str, format: str = FORMAT_STRING, split_weeks: bool = False) -> str:
        """Process a given date range string and return a formatted date range string.

        Args:
            date_range (str): The date range string to process. Supported formats include:
                - "standard_periods"
                - "relative_days"
                - "quarters"
                - "years"
                - "custom" (e.g., "10_days_ago", "2_weeks_ago", "3_months_ago")
            format (str, optional): The format string to use for the output. Defaults to FORMAT_STRING.
            split_weeks (bool, optional): If True and the resulting period spans more than one week,
                also include a 'weeks' array with Sunday-to-Saturday splits for the recent weeks.

        Returns:
            str: A formatted date range string or an error message if the date range is unsupported or an error occurs.
        """
        today = datetime.now()

        try:
            handlers: dict[str, Callable] = {
                "standard_periods": lambda: self._get_standard_period_dates(date_range, today),
                "relative_days": lambda: self._get_relative_day_dates(date_range, today),
                # Only handle special tokens 'this_quarter' and 'last_quarter' here. Natural forms like 'Q1 2025'
                # are parsed later by _parse_month_or_range(). For non-matching inputs, return None so we keep trying.
                "quarters": lambda: (
                    self._get_quarter_dates(today, last_quarter=(date_range == "last_quarter"))
                    if date_range in {"this_quarter", "last_quarter"}
                    else None
                ),
                "years": lambda: self._get_year_dates(date_range, today),
                "custom": lambda: (
                    self._parse_custom_range(date_range)
                    if re.match(r"\d+_(days|weeks|months)_ago", date_range)
                    else None
                ),
            }

            for handler in handlers.values():
                try:
                    result = handler()
                    if result:
                        return self._get_result_and_format(date_range, format, split_weeks, result)
                except ValueError:
                    continue

            # Try parsing natural month/quarter expressions
            mr = self._parse_month_or_range(date_range)
            if mr:
                return self._get_result_and_format(date_range, format, split_weeks, mr)

            return (
                f"Unsupported date range: {date_range}, supported date ranges are: {SUPPORTED_DATE_RANGES} "
                f"or natural month/quarter forms like 'January 2025', 'January-March 2025', 'Q1 2025'."
            )

        except Exception as e:
            return f"Error processing date range: {str(e)}"
