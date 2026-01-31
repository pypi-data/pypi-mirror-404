from langchain_core.tools import BaseTool
from pydantic import BaseModel

FORMAT_STRING: str
DEFAULT_TIMEZONE: str

class TimeToolInput(BaseModel):
    """Input schema for the TimeTool."""
    datetime_format: str
    timezone: str | None

class TimeTool(BaseTool):
    """Tool to get the current time."""
    name: str
    description: str
    args_schema: type[BaseModel]
