import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    SQLiteSession,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp

load_dotenv()

app = FastAPI()

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")
model_name = os.getenv("NVIDIA_MODEL")
tavily_api_key = os.getenv("TAVILY_API_KEY")
sample_dir = Path(__file__).resolve().parent / "sample_files"
session_db = Path(__file__).resolve().parent / "conversations.db"

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
)

model = OpenAIChatCompletionsModel(
    model=model_name,
    openai_client=client,
)

set_tracing_disabled(True)


class ChatRequest(BaseModel):
    query: str
    session_id: str


@app.get("/")
def root():
    return {"message": "Agent API is running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
        raise ValueError("Set TAVILY_API_KEY in your local .env before using /chat.")

    async with (
        MCPServerStdio(
            name="Filesystem MCP",
            params={
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(sample_dir),
                ],
            },
        ) as filesystem_server,
        MCPServerStreamableHttp(
            name="Tavily MCP",
            params={
                "url": "https://mcp.tavily.com/mcp/",
                "headers": {"Authorization": f"Bearer {tavily_api_key}"},
            },
            client_session_timeout_seconds=60,
        ) as tavily_server,
    ):
        agent = Agent(
            name="MCP Agent",
            instructions=(
                "You are a helpful AI assistant. Keep responses clear and concise. "
                f"Use filesystem tools for files under {sample_dir}. "
                "Use Tavily search for web research and include source URLs. "
                "Use both when a query needs local files and web information. "
                "Answer directly when no tool is needed. "
                "Once you have enough information, provide the final answer."
            ),
            model=model,
            mcp_servers=[filesystem_server, tavily_server],
        )
        session = SQLiteSession(request.session_id, session_db)
        try:
            result = await Runner.run(agent, request.query, session=session)
        finally:
            session.close()
        for item in result.new_items:
            if item.type == "tool_call_item":
                print("Tool called:", item.raw_item.name, flush=True)
            elif item.type == "tool_call_output_item":
                print("Tool output:", item.output, flush=True)

    return {
        "response": result.final_output
    }
