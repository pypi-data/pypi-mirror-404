from _typeshed import Incomplete
from aip_agents.memory.constants import MemoryDefaults as MemoryDefaults
from aip_agents.tools.memory_search.base import LongTermMemorySearchTool as LongTermMemorySearchTool
from aip_agents.tools.memory_search.schema import LongTermMemoryDeleteInput as LongTermMemoryDeleteInput, LongTermMemorySearchInput as LongTermMemorySearchInput
from aip_agents.utils.datetime import is_valid_date_string as is_valid_date_string, next_day_iso as next_day_iso
from aip_agents.utils.logger import get_logger as get_logger
from typing import ClassVar

logger: Incomplete
MEMORY_SEARCH_TOOL_NAME: str
MEMORY_DELETE_TOOL_NAME: str

class Mem0SearchTool(LongTermMemorySearchTool):
    """Mem0-specific implementation of the long-term memory search tool."""
    name: str
    description: str
    args_schema: type[LongTermMemorySearchInput]
    LOG_PREFIX: ClassVar[str]
    METADATA_FILTER_BLOCKLIST: ClassVar[set[str]]
Mem0SearchInput = LongTermMemorySearchInput

class Mem0DeleteTool(LongTermMemorySearchTool):
    """Mem0-specific implementation of the long-term memory delete tool."""
    name: str
    description: str
    args_schema: type[LongTermMemoryDeleteInput]
    LOG_PREFIX: ClassVar[str]
    METADATA_FILTER_BLOCKLIST: ClassVar[set[str]]
Mem0DeleteInput = LongTermMemoryDeleteInput
