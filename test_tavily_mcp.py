import os
import asyncio

from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStreamableHttp


load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")
model_name = os.getenv("NVIDIA_MODEL")
tavily_api_key = os.getenv("TAVILY_API_KEY")

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
)

model = OpenAIChatCompletionsModel(
    model=model_name,
    openai_client=client,
)

set_tracing_disabled(True)


async def main():
    if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
        raise ValueError("Set TAVILY_API_KEY in your local .env before running this test.")

    async with MCPServerStreamableHttp(
        name="Tavily MCP",
        params={
            "url": "https://mcp.tavily.com/mcp/",
            "headers": {"Authorization": f"Bearer {tavily_api_key}"},
        },
        client_session_timeout_seconds=60,
    ) as server:
        tools = await server.list_tools()
        print("Available MCP tools:", ", ".join(tool.name for tool in tools))

        search_tool = next(
            tool for tool in tools
            if tool.name.replace("-", "_") == "tavily_search"
        )
        print("\n--- Direct Tavily search (before agent run) ---", flush=True)
        print("Tool:", search_tool.name, flush=True)
        search_result = await server.call_tool(
            search_tool.name,
            {"query": "official Model Context Protocol documentation"},
        )
        print("isError:", search_result.model_dump(by_alias=True)["isError"])
        print("Full MCP result:")
        print(search_result.model_dump_json(by_alias=True, indent=2), flush=True)
        print("\n--- Agent test ---", flush=True)

        agent = Agent(
            name="Tavily Search Agent",
            instructions=(
                "You are a helpful assistant. "
                "When the user asks for web research, use the Tavily search tool "
                "instead of guessing. Keep responses concise and include source URLs."
            ),
            model=model,
            mcp_servers=[server],
        )

        result = await Runner.run(
            agent,
            "Search the web for the official Model Context Protocol documentation. "
            "Summarize what MCP is in two sentences and include the source URL.",
        )

        for item in result.new_items:
            if item.type == "tool_call_item":
                print("Tool called:", item.raw_item.name)
            elif item.type == "tool_call_output_item":
                print("Tool output:", item.output)

        print("\nFinal response:")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
