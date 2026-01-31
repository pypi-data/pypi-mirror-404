"""Minimal PTC hello world example.

Required environment variables:
- OPENAI_API_KEY
- E2B_API_KEY
"""

import asyncio

from aip_agents.agent import LangGraphReactAgent
from aip_agents.ptc import PromptConfig, PTCSandboxConfig


async def main() -> None:
    """Run a hello-world PTC flow."""
    instruction = (
        "You are a helpful assistant with access to execute_ptc_code. "
        "Use execute_ptc_code to run Python and print output. "
        "The tool returns JSON with ok/stdout/stderr/exit_code."
    )

    agent = LangGraphReactAgent(
        name="ptc_hello_world",
        instruction=instruction,
        model="openai/gpt-5.2",
        ptc_config=PTCSandboxConfig(enabled=True, sandbox_timeout=180.0, prompt=PromptConfig(mode="index")),
    )
    agent.add_mcp_server(
        {
            "deepwiki": {
                "transport": "streamable-http",
                "url": "https://mcp.deepwiki.com/mcp",
                "headers": {},
                "timeout": 60.0,
            }
        }
    )

    try:
        response = await agent.arun(
            query="Use execute_ptc_code to print 'Hello, world!' and count the number of words in the output of deepwiki.read_wiki_structure('anthropics/claude-code')."
        )
        print("execute_ptc_code output:", response["output"])
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
