import os
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import httpx2
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from mcp.types import CallToolResult
from mcp.shared.exceptions import MCPError
from mcp.client.stdio import stdio_client
from agents import (
    Agent,
    Runner,
    SQLiteSession,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
from agents.exceptions import UserError

logger = logging.getLogger("uvicorn.error")
# Upstream diagnostics can include tool arguments, URLs, or response bodies.
for library in ("openai", "mcp", "httpx2", "httpcore2"):
    logging.getLogger(library).setLevel(logging.CRITICAL + 1)


class MCPToolExecutionError(UserError):
    pass


class CheckedMCPTools:
    async def call_tool(self, tool_name, arguments, meta=None):
        result = await super().call_tool(tool_name, arguments, meta=meta)
        # Validate the MCP envelope; text content need not itself be JSON.
        result = CallToolResult.model_validate(result)
        if result.model_dump(by_alias=True)["isError"]:
            raise MCPToolExecutionError("The MCP server reported a tool execution failure.")
        return result


class CheckedFilesystemMCP(CheckedMCPTools, MCPServerStdio):
    @asynccontextmanager
    async def create_streams(self):
        with open(os.devnull, "w") as errlog:
            async with stdio_client(self.params, errlog=errlog) as streams:
                yield streams


class CheckedTavilyMCP(CheckedMCPTools, MCPServerStreamableHttp):
    pass


class CheckedWeatherMCP(CheckedFilesystemMCP):
    pass


def error_causes(error):
    """Include transport task-group errors and SDK-wrapped exceptions."""
    yield error
    if isinstance(error, BaseExceptionGroup):
        for child in error.exceptions:
            yield from error_causes(child)
    cause = error.__cause__ or error.__context__
    if cause is not None:
        yield from error_causes(cause)

load_dotenv()

app = FastAPI()

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")
model_name = os.getenv("NVIDIA_MODEL")
tavily_api_key = os.getenv("TAVILY_API_KEY")
sample_dir = Path(__file__).resolve().parent / "sample_files"
session_db = Path(__file__).resolve().parent / "conversations.db"
installed_mcp = os.getenv("MCP_USE_INSTALLED", "0") == "1"

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
    try:
        return await run_chat(request)
    except Exception as error:
        causes = list(error_causes(error))
        if any(isinstance(e, MCPToolExecutionError) for e in causes):
            status, message = 502, "An MCP tool could not complete the requested operation."
        elif any(isinstance(e, (ValidationError, json.JSONDecodeError)) for e in causes):
            status, message = 502, "A service returned an invalid response. Please try again."
        elif any(isinstance(e, (OSError, TimeoutError, httpx2.HTTPError,
                               anyio.EndOfStream, anyio.BrokenResourceError,
                               anyio.ClosedResourceError))
                 or (isinstance(e, MCPError) and e.code in (-32000, -32001))
                 for e in causes):
            status, message = 503, "A required service connection failed. Please try again."
        else:
            status, message = 502, "The agent could not complete this request. Please try again."
        # Avoid exposing credentials or upstream payloads in error messages.
        logger.warning("Chat failed status=%s exception_types=%s", status,
                       [type(e).__name__ for e in causes])
        return JSONResponse(status_code=status, content={"response": message})


async def run_chat(request: ChatRequest):
    if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
        return JSONResponse(status_code=503, content={
            "response": "Tavily is not configured. Set TAVILY_API_KEY on the server."
        })

    async with (
        CheckedFilesystemMCP(
            name="Filesystem MCP",
            failure_error_function=None,
            params={
                "command": "mcp-server-filesystem" if installed_mcp else "npx",
                "args": [str(sample_dir)] if installed_mcp else [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(sample_dir),
                ],
            },
        ) as filesystem_server,
        CheckedTavilyMCP(
            name="Tavily MCP",
            failure_error_function=None,
            params={
                "url": "https://mcp.tavily.com/mcp/",
                "headers": {"Authorization": f"Bearer {tavily_api_key}"},
            },
            client_session_timeout_seconds=60,
        ) as tavily_server,
        CheckedWeatherMCP(
            name="Open-Meteo Weather MCP",
            failure_error_function=None,
            params={
                "command": "open-meteo-mcp-server" if installed_mcp else "npx",
                "args": [] if installed_mcp else ["-y", "-p", "open-meteo-mcp-server@2.5.2",
                         "open-meteo-mcp-server"],
            },
            client_session_timeout_seconds=60,
        ) as weather_server,
    ):
        agent = Agent(
            name="MCP Agent",
            instructions=(
                "You are a helpful AI assistant. Keep responses clear and concise. "
                f"Use filesystem tools for files under {sample_dir}. "
                "Use Tavily search for web research and include source URLs. "
                "Use Open-Meteo tools for weather; resolve place names with geocoding "
                "and use weather_forecast for current conditions and forecasts. "
                "Combine tools when a query needs multiple sources. "
                "Answer directly when no tool is needed. "
                "Once you have enough information, provide the final answer."
            ),
            model=model,
            mcp_servers=[filesystem_server, tavily_server, weather_server],
        )
        session = SQLiteSession(request.session_id, session_db)
        try:
            previous_history = await session.get_items()
            try:
                result = await Runner.run(agent, request.query, session=session)
            except Exception:
                # The SDK saves input before running; discard an incomplete failed turn.
                await session.clear_session()
                await session.add_items(previous_history)
                raise
        finally:
            session.close()
        for item in result.new_items:
            if item.type == "tool_call_item":
                logger.info("Tool called: %s", item.raw_item.name)

    return {
        "response": result.final_output
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")),
                workers=1, access_log=False)
