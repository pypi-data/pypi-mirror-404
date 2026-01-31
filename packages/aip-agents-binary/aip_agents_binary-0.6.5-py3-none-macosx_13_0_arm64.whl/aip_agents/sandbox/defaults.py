"""Defaults for PTC sandbox templates and packages."""

DEFAULT_PTC_TEMPLATE = "aip-agents-ptc-v1"
DEFAULT_PTC_PACKAGES: tuple[str, ...] = (
    "aip-agents-binary[local]",
    "mcp",
    "httpx",
    "gllm-plugin-binary==0.0.7",
)
