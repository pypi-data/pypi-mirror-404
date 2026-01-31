"""Minimal LangGraph agent with GL Connectors support example demonstrating asynchronous run.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.tools import GL_CONNECTORS_AUTOMATED_TOOLS

load_dotenv(override=True)


async def langgraph_gl_connector_example():
    """Demonstrates the LangGraphAgent's arun method."""
    model = ChatOpenAI(model="gpt-4.1", temperature=0)
    agent_name = "GLConnectorTwitterAgent"

    langgraph_agent = LangGraphAgent(
        name=agent_name,
        instruction="You are a helpful assistant that uses GL Connectors to connect with the Twitter API.",
        model=model,
        tools=GL_CONNECTORS_AUTOMATED_TOOLS["twitter"],
    )

    query = "Get 3 tweets about the latest Air India Incident"
    print(f"--- Agent: {agent_name} ---")
    print(f"Query: {query}")

    print("\nRunning arun...")
    response = await langgraph_agent.arun(
        query=query,
        configurable={"configurable": {"thread_id": "lgraph_arith_example_arun"}},
    )
    print(f"[arun] Final Response: {response['output']}")
    print("--- End of LangGraph Example ---")


if __name__ == "__main__":
    asyncio.run(langgraph_gl_connector_example())
