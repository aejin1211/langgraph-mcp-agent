# PROCESS_LOG

## AI Tools Used

I used ChatGPT and OpenAI Codex during this assignment.

ChatGPT helped me understand the assignment requirements, MCP concepts, and the overall project structure.

Codex helped me make small code changes, run tests, and check the deployment setup.

## Development Narrative

I first built a basic FastAPI `/chat` endpoint and connected it to NVIDIA NIM through the OpenAI Agents SDK. After that, I added the Filesystem MCP server and checked that the agent could read a local file.

Next, I added Tavily Search MCP. At first, the agent reached the maximum number of turns. I tested Tavily directly to check whether the MCP server itself was working. One prompt I used was: “First, test the Tavily search tool directly before Runner.run(). Print the tool result clearly. Keep the agent test after that. Do not increase max_turns.” The direct test worked, so I knew the MCP connection itself was working even though the agent loop had failed to finish.

Then I connected Filesystem and Tavily to the same agent and added SQLiteSession memory using `session_id`. I also tested whether different sessions stayed separate.

After that, I added Open-Meteo as a third MCP server for weather queries. I tested geocoding and weather forecast tools before using them through the agent.

I then worked on error handling. I tested connection failures, tool errors, and invalid MCP responses. I found that a failed request could remain in the session history, so I restored the previous history when a request failed.

Finally, I ran regression tests, built the Docker image, tested the container, and deployed the project to Google Cloud Run.

## Verification

I tested the project in several ways instead of only running one successful request.

I tested no-tool questions, file reading, web search, weather, multi-step tool use, same-session memory, and session isolation.

For failure handling, connection and timeout errors and malformed MCP responses were tested with controlled local or Docker tests. I also triggered a real missing-file tool failure.

After deployment, I tested the public Cloud Run service. I verified the three MCP servers, multi-step tool use, memory, session isolation, a missing-file tool failure, and successful memory recovery after that failure.

## What I Learned

I learned that a successful MCP connection does not mean the whole agent flow is working correctly. When Tavily worked directly but the agent reached the turn limit, I had to separate the MCP tool test from the agent loop to understand where the problem was.

I also learned that failed requests can affect conversation memory. I had to inspect how the SDK saved session history and make sure a failed turn did not cause the next request to repeat the same failed action.