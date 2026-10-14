import os
import asyncio

from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


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

agent = Agent(
    name="NIM Test Agent",
    instructions="You are a helpful assistant. Keep responses concise.",
    model=model,
)

set_tracing_disabled(True)


async def main():
    result = await Runner.run(
        agent,
        "Explain what an AI agent is in one sentence.",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())