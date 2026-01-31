from pydantic import BaseModel
from typing import Any

class MemoryConfig(BaseModel):
    """Tool configuration schema for memory operations."""
    user_id: str

class LongTermMemorySearchInput(BaseModel):
    """Input schema for unified long-term memory retrieval."""
    query: str | None
    start_date: str | None
    end_date: str | None
    limit: int | None
    categories: list[str] | None
    metadata: dict[str, Any] | None

class LongTermMemoryDeleteInput(BaseModel):
    """Input schema for unified long-term memory deletion."""
    query: str | None
    memory_ids: list[str] | None
    delete_all: bool | None
    top_k: int | None
    threshold: float | None
    categories: list[str] | None
    metadata: dict[str, Any] | None
