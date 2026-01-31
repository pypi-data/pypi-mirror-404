"""Simple A2A client demonstrating tool output management.

This client connects to the data visualization server and demonstrates
how tools can reference each other's outputs using the tool output
management system.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio

from dotenv import load_dotenv

from aip_agents.agent import LangGraphReactAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main():
    """Demonstrate tool output management with data visualization."""
    # Create client agent
    client = LangGraphReactAgent(
        name="Client",
        instruction="You request data visualization services.",
        model="openai/gpt-4o-mini",
    )

    # Discover server agent
    agents = client.discover_agents(A2AClientConfig(discovery_urls=["http://localhost:8885"]))
    server_agent = agents[0]

    async for chunk in client.astream_to_agent(
        server_agent,
        "Generate sales data for 1000 months and create a bar chart from it",
    ):
        if chunk.get("content"):
            print(chunk["content"], end="", flush=True)
        if chunk.get("metadata"):
            print(f"\nMetadata: {chunk['metadata']}", end="\n\n", flush=True)
        tool_info = chunk.get("metadata", {}).get("tool_info") if isinstance(chunk.get("metadata"), dict) else None
        if isinstance(tool_info, dict):
            for tool_call in tool_info.get("tool_calls", []):
                if tool_call.get("name") == "data_visualizer":
                    data_source = tool_call.get("args", {}).get("data_source")
                    if not (isinstance(data_source, str) and data_source.startswith("$tool_output.")):
                        raise RuntimeError(
                            "Tool output sharing failed: expected data_source to reference $tool_output.<call_id>."
                        )
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
