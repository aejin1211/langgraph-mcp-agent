# Process Log

Short chronological notes on material development events, recorded from October 14, 2026 onward.

Each entry will include:
- **Goal:** What we were trying to accomplish.
- **Change:** What was implemented or changed.
- **Verification:** What was tested and the result, including anything not yet verified.
- **Issue or decision:** Any important problem, tradeoff, or implementation decision.
- **AI prompt:** The prompt or relevant excerpt when it materially affected implementation.

Entries distinguish user-reported results from checks performed by the assistant. These development notes are a basis for the assignment's process narrative; personal reflections should be written by the student.

## October 14, 2026 — Direct Tavily search diagnostic

- **Goal:** Separate Tavily tool execution from the agent loop after the user reported successful tool discovery followed by `MaxTurnsExceeded` at 10 turns.
- **Change:** Added a direct call to the discovered Tavily search tool before the existing agent test. Print the tool name, MCP error flag, and full formatted result. Kept the agent test and turn limit unchanged.
- **Verification:** Local syntax, SDK call-signature, and result-formatting checks passed after correcting the error-flag access. No live search or agent run was performed by the assistant; runtime verification remains pending.
- **Issue or decision:** The installed MCP SDK uses `is_error` as its Python field name. An initial formatting check failed using `isError`; serialization with protocol aliases now reads and prints `isError` correctly. Direct results print before `Runner.run()`, so a later agent failure will not hide them.
- **AI prompt:** “First, test the Tavily search tool directly before Runner.run(). Print the tool result clearly. Keep the agent test after that. Do not increase max_turns.” The user approved this limited change before editing.

## October 14, 2026 — Tavily runtime verification succeeded

- **Goal:** Verify direct Tavily search and automatic agent tool use independently.
- **Change:** No implementation changes; recorded the user's terminal output.
- **Verification:** The user ran `python3 test_tavily_mcp.py`. Tool discovery returned five tools. The direct `tavily_search` call returned `isError: False` and populated search results. The subsequent agent run selected `tavily_search`, received search results, and produced a final answer within the unchanged turn limit.
- **Issue or decision:** The previous `MaxTurnsExceeded` did not recur in this run; its cause remains unconfirmed. The final answer cited `modelcontextprotocol.info/docs`, while the returned GitHub excerpt identifies `modelcontextprotocol.io` as the official documentation site. Tool execution succeeded, but official-source selection still needs care. The standalone test remains separate from `main.py`.
- **AI prompt:** No new implementation prompt; the user supplied runtime output for interpretation.

## October 14, 2026 — Combined filesystem and Tavily agent

- **Goal:** Make both verified MCP servers available to the `/chat` agent.
- **Change:** Updated `main.py` to open filesystem stdio and Tavily HTTP MCP connections inside the request handler and attach both to one NIM-backed agent. Added instructions for file queries, web research, combined queries, and finishing once sufficient information is available.
- **Verification:** Syntax and mocked handler checks passed: both servers were attached to the agent, the query and response were preserved, and both connections closed after the request. The root handler also passed. Combined live API behavior has not yet been tested.
- **Issue or decision:** Used request-scoped async context managers to keep the change small and ensure connection cleanup in the same task. This starts/connects both servers for each request, adding overhead. No memory was added; `session_id` remains accepted but unused. The turn limit is unchanged.
- **AI prompt:** “please combine the filesystem mcp and tavily mcp in one agent. Keep the changes small and write it into main.py. Do not add memroy yet.”

## October 14, 2026 — API tool debug prints

- **Goal:** See which tools the combined agent calls and what they return.
- **Change:** Added flushed `Tool called:` and `Tool output:` prints for `result.new_items` in `main.py`, matching the standalone test style.
- **Verification:** Python syntax check passed. No live API call was performed.
- **Issue or decision:** Prints appear in the server terminal after `Runner.run()` completes successfully; they will not appear if the run raises before returning. The HTTP response and agent behavior are unchanged.
- **AI prompt:** “Add debug prints in main.py to show which tool was called and its output.”

## October 14, 2026 — SDK conversational memory

- **Goal:** Keep conversation history across requests using the SDK's built-in session feature, keyed by `request.session_id`.
- **Change:** Added `SQLiteSession(request.session_id, session_db)` to `main.py` and passed it to `Runner.run`. Close the session connection in `finally`. Added `conversations.db*` to `.gitignore`.
- **Verification:** Local checks passed for syntax, real SQLite history retained after reopening a session, isolation of different session IDs, and mocked handler wiring with the correct SDK session. No live NIM/MCP call was made; model recall over HTTP remains to be verified.
- **Issue or decision:** Use a shared SQLite file outside the filesystem MCP's allowed root so separate request-scoped session objects retain history without a custom dictionary. History survives local restarts while the database file remains. Followed the SDK session pattern documented at https://developers.openai.com/api/docs/guides/agents/running-agents.
- **AI prompt:** “add conversational memeory to main.py using the OpenAI agents sdk built-in session feature and reuqest.session)id. Do not use a custom dictionary.”

## October 14, 2026 — Graceful MCP failure handling

- **Goal:** Handle connection failures, tool execution errors, and invalid responses without an unhandled HTTP server error.
- **Change:** Added checked MCP subclasses that validate tool-result envelopes and detect `isError`. Disabled SDK conversion of raised tool errors into model-visible retry messages so failures reach the HTTP handler. Added safe JSON error responses (503 for recognized connection failures; 502 for tool, validation, and other agent failures), including nested/wrapped exceptions. Missing Tavily configuration returns 503. Successful MCP calls, debug prints, and SQLite session wiring remain unchanged.
- **Verification:** Local simulated checks passed for both server wrappers, valid text results, `isError` results, invalid envelopes, JSON decoding errors, grouped transport errors, HTTP status/body behavior, existing SQLite history access, and resource cleanup on successful and failed runs. No live MCP/NIM calls were made.
- **Issue or decision:** The first check found `httpx` absent; this environment uses `httpx2`, so handling now imports the installed transport dependency. Errors terminate the failed request with a clear response rather than asking the model to retry indefinitely. SQLite connections still close in `finally`; stored history is not cleared. Error responses omit upstream payloads and credentials.
- **AI prompt:** “add graceful MCP error handling to main.py. handle connection errors, tool execution errors, and invalid response. Keep the current mcp and memory behavior unchanged.”

## October 14, 2026 — Explicit transport dependency name

- **Goal/change:** Replaced `import httpx2 as httpx` with `import httpx2` and updated the exception reference to `httpx2.HTTPError` for clarity. No behavior changed.
- **Verification:** Syntax and exception import checks passed; no live calls made.
- **Decision/prompt:** The user requested: “change it to import httpx2 and use httpx2.HTTPError. Keep everything else unchanged.”

## October 14, 2026 — Inspect wrapped connection errors

- **Goal:** Investigate the user's connection test reporting `UserError` by exposing inner exception types.
- **Change:** Print the fully qualified type of every exception returned by `error_causes()` before classification. Error responses and classification remain unchanged; exception messages are not printed.
- **Verification:** Syntax check passed. The user must rerun the connection test to identify the actual inner cause; no live test was performed here.
- **AI prompt:** “Please print all exception types found by error_causes() so we can see the inner cause.”

## October 14, 2026 — Malformed MCP response test

- **Goal/change:** Added standalone `test_malformed_mcp.py`, validating a `CallToolResult` with a string instead of a list in `content`. The test fails if validation unexpectedly succeeds.
- **Verification:** Ran `.venv/bin/python -B test_malformed_mcp.py`; passed with the expected Pydantic `ValidationError` identifying `content` as an invalid list. No network calls or credentials were needed.
- **Decision:** This checks MCP response-schema validation only; it does not simulate a live server or test the HTTP error handler. `main.py` is unchanged.
- **AI prompt:** “add a small separate test for malformed MCP responses. Trigger a ValidationError by validating an invalid CallToolResult.”

## October 14, 2026 — Open-Meteo third MCP server

- **Goal:** Add free, no-key weather tools as the third MCP server.
- **Change:** Added `CheckedWeatherMCP` to `main.py`, reusing the existing result validation and error handling. Launch `open-meteo-mcp-server@2.5.2` with npx over stdio and attach it to the same agent. Added weather/geocoding instructions. README documents the external implementation, rationale, Node requirement, and sample request.
- **Verification:** npm metadata confirmed version 2.5.2 requires Node 22+; installed Node is 24.11.0. Real MCP discovery returned 17 tools; direct `geocoding` for Los Angeles succeeded. A real `weather_forecast` call through the checked class returned numeric current temperature and units. Mocked handler checks passed for all three servers, session ID, response format, and cleanup. NIM-driven weather selection through `/chat` remains unverified.
- **Issue or decision:** Selected https://github.com/cmer81/open-meteo-mcp for stdio support and no-key non-commercial Open-Meteo access. Pinned the package version; no new Python dependency or credential. Initial npm access failed under sandbox networking; approved network access allowed metadata and runtime verification. Existing memory and other MCP configuration remain unchanged.
- **AI prompt:** “Please add Open-Meteo Weather MCP as the third MCP server. Use a free implementation with no API key, as recommended in the assignment. Keep it as simple as possible.”

## October 15, 2026 — Fix transport classification and failed-turn memory

- **Goal:** Fix the two failed local regression cases: MCP transport codes fell through to generic 502, and a failed file request polluted the next conversation turn.
- **Change:** Recognize installed SDK `MCPError` codes -32000 and -32001 as transport failures (503). Snapshot SQLiteSession history before Runner.run and restore it through SDK methods when the run raises, preserving prior successful conversation history. Successful writes and existing server configuration are unchanged.
- **Verification:** Local checks passed for wrapped transport errors, unchanged treatment of other MCP codes, failed-turn rollback, subsequent history access, and successful writes. A live NIM/MCP sequence passed: store codename (200), fail a nonexistent-file read (502), verify exact history restoration, then recall the codename (200) with no tool calls. Used a temporary database; existing conversations were not altered.
- **Issue or decision:** Restore history only for failed runs; this does not undo external tool side effects or clean up previously stored failed turns. Verification covers sequential requests, not overlapping requests with the same session ID.
- **AI prompt:** “Please fix only the two failed regression cases: 1. Treat MCPError codes -32000 and -32001 as connection/transport failures. 2. Prevent a failed request from causing the next same-session request to repeat the failed tool action. Keep all existing behavior unchanged.”

## October 15, 2026 — Prepare and locally verify deployment

- **Goal/change:** Added Dockerfile, minimal pinned Python requirements, Docker/Cloud Build ignore files, environment template, and deployment script; expanded README with local/container/deployment steps. Made the environment template trackable. Container builds install the two stdio MCP servers ahead of time; main.py selects those executables in Docker and retains npx locally. Added PORT-aware Uvicorn startup. Replaced debug output with tool-name/error-type logging and suppressed upstream payload diagnostics and stdio server stderr to avoid logging queries or secrets. Request-scoped connections, SQLiteSession, rollback, and response/status behavior remain unchanged.
- **Verification:** Built `csci599-a1:local` successfully for linux/amd64. Container checks passed for non-root execution, writable application directory, installed MCP executables, exclusion of credentials/history, and injected PORT=9090. Live HTTP tests passed for health, no-tool answers, filesystem, Tavily, weather, multi-step tools, same-session memory, and isolation. Controlled closed-connection (-32000), timeout (-32001), missing executable, tool isError, and malformed-result tests returned expected 503/502 responses and preserved history. An explicit real missing-file read returned 502, followed by successful memory recall (200). Local npx discovery of all three servers, standalone malformed-response validation, syntax checks, and git diff whitespace checks passed.
- **Issue/decision:** Docker Desktop initially was stopped; started it for the build. One broadly worded live missing-file test returned 200 rather than the expected 502; this did not establish that a failing tool was actually invoked. Retested with an explicit direct-read instruction, which produced the expected failure and successful subsequent recall. Tests used container/temporary SQLite history, preserving local conversations. Removed the temporary test container; retained the built image. Cloud Run deployment has not been executed. SQLite remains instance-local; deployment defaults to concurrency 1 and maximum 1 instance.
- **AI prompt:** “Approved. Please proceed with the proposed deployment files and minimal main.py changes. Keep local development working, and keep requirements.txt limited to the dependencies actually needed by this project. After the changes, do not deploy yet. First build and test the Docker image locally and report the results.”
