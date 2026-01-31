from _typeshed import Incomplete
from collections.abc import Callable as Callable
from langchain_core.tools import BaseTool
from pydantic import BaseModel

FORMAT_STRING: str
MIN_DAYS_FOR_WEEK_SPLIT: int
MONTH_NAME_ABBR_THRESHOLD: int
SUPPORTED_DATE_RANGES: Incomplete

class DateRangeToolInput(BaseModel):
    """Input schema for the DateRangeTool."""
    date_range: str
    format: str
    split_weeks: bool

class DateRangeTool(BaseTool):
    """Tool to get date ranges for common time periods."""
    name: str
    description: str
    args_schema: type[BaseModel]
