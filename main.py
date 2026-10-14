import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)

load_dotenv()

app = FastAPI()

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
    name="MCP Agent",
    instructions="You are a helpful AI assistant. Keep responses clear and concise.",
    model=model,
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
    result = await Runner.run(
        agent,
        request.query,
    )

    return {
        "response": result.final_output
    }