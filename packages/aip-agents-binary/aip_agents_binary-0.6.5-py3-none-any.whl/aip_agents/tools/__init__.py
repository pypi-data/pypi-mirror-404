"""Initialize Tools Module for AIP Agents."""

from importlib import import_module
from typing import TYPE_CHECKING

from aip_agents.tools.date_range_tool import DateRangeTool
from aip_agents.tools.gl_connector import GLConnectorTool
from aip_agents.tools.gl_connector_tools import (
    BOSA_AUTOMATED_TOOLS,
    GL_CONNECTORS_AUTOMATED_TOOLS,
)
from aip_agents.tools.time_tool import TimeTool
from aip_agents.tools.web_search import GoogleSerperTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = [
    "BOSA_AUTOMATED_TOOLS",
    "GL_CONNECTORS_AUTOMATED_TOOLS",
    "GLConnectorTool",
    "GoogleSerperTool",
    "TimeTool",
    "DateRangeTool",
]


def _register_optional(module_path: str, export_name: str) -> None:
    """Try to import optional tool module and expose it in __all__.

    Args:
        module_path: The module path to import.
        export_name: The name to export in __all__.
    """
    try:
        module = import_module(module_path)
        tool = getattr(module, export_name)
        __all__.append(export_name)
        globals()[export_name] = tool

    except ImportError as e:
        logger.debug(f"Module {module_path} not found: {e}")
    except AttributeError as e:
        logger.debug(f"Tool {export_name} not found in module {module_path}: {e}")
    except Exception as e:
        logger.debug(f"Unexpected error loading {export_name}: {e}")


_register_optional("aip_agents.tools.browser_use", "BrowserUseTool")
_register_optional("aip_agents.tools.code_sandbox", "E2BCodeSandboxTool")
_register_optional("aip_agents.tools.document_loader", "DocxReaderTool")
_register_optional("aip_agents.tools.document_loader", "ExcelReaderTool")
_register_optional("aip_agents.tools.document_loader", "PDFReaderTool")
_register_optional("aip_agents.tools.execute_ptc_code", "create_execute_ptc_code_tool")

if TYPE_CHECKING:
    from aip_agents.tools.browser_use import BrowserUseTool
    from aip_agents.tools.code_sandbox import E2BCodeSandboxTool
    from aip_agents.tools.document_loader import (
        DocxReaderTool,
        ExcelReaderTool,
        PDFReaderTool,
    )
    from aip_agents.tools.execute_ptc_code import create_execute_ptc_code_tool
