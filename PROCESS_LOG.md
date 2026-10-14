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
