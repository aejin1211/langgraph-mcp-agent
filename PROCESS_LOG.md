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
