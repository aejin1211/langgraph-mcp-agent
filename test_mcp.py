import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio


load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")
model_name = os.getenv("NVIDIA_MODEL")

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
)

model = OpenAIChatCompletionsModel(
    model=model_name,
    openai_client=client,
)

set_tracing_disabled(True)

current_dir = Path(__file__).parent
sample_dir = current_dir / "sample_files"


async def main():
    async with MCPServerStdio(
        name="Filesystem MCP",
        params={
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(sample_dir),
            ],
        },
    ) as server:

        agent = Agent(
            name="Filesystem Agent",
            instructions=(
                "You are a helpful assistant. "
                "When the user asks about files, use the filesystem tools "
                "instead of guessing."
            ),
            model=model,
            mcp_servers=[server],
        )

        result = await Runner.run(
            agent,
            "What does notes.txt say?",
        )

        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())