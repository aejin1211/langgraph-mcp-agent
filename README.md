# langgraph-mcp-agent

The agent connects to filesystem, Tavily Search, and Open-Meteo Weather MCP servers.

Weather uses [cmer81/open-meteo-mcp](https://github.com/cmer81/open-meteo-mcp),
an MIT-licensed implementation, via `open-meteo-mcp-server@2.5.2` over stdio.
It adds location lookup, current conditions, and forecasts without relying on web search.
Open-Meteo is free for non-commercial use and requires no API key.
Node.js 22+ and npm/npx are required; npx downloads the package on first use.
No new Python dependency or environment variable is needed for weather.

Other external servers: [filesystem MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
and [Tavily MCP](https://github.com/tavily-ai/tavily-mcp).

## Local development

Use Python 3.13 and Node.js 22+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Only on first setup; preserve existing credentials.
# Edit .env with your NVIDIA and Tavily credentials.
python main.py
```

The service listens on `http://localhost:8080` by default. Set `PORT` to override it.
For reload during development: `.venv/bin/uvicorn main:app --reload --port 8080 --no-access-log`.
Local development uses npx; the Docker image uses MCP executables installed at build time.
SQLiteSession stores history in `conversations.db`, keyed by `session_id`.
Send requests sequentially when sharing a session ID.

## Docker

```bash
docker build --platform linux/amd64 -t csci599-a1:local .
docker run --rm --name csci599-a1-local --env-file .env \
  -p 8080:8080 csci599-a1:local
```

The image runs as a non-root user and includes Node 24, filesystem MCP 1.0.0,
and Open-Meteo MCP 2.5.2. It does not include `.env`, your virtualenv, or local history.
For a different container port, pass `-e PORT=9090 -p 9090:9090` instead.
API keys are supplied only at runtime. Do not pass them as build arguments.

Check the running service:

```bash
curl http://localhost:8080/
curl http://localhost:8080/chat -H 'Content-Type: application/json' \
  -d '{"query":"What is 17 plus 25?","session_id":"smoke"}'
```

Verify file reads, search, weather, multi-step tool use, memory across two turns,
session isolation, controlled MCP failures, and recall after a failed request.
`python test_malformed_mcp.py` separately checks invalid MCP result validation.
Application logs contain tool names and error types/statuses, not query text or tool outputs.

## Cloud Run deployment (run only when ready)

Authenticate gcloud and select your billed GCP project. Enable the required APIs:

```bash
gcloud auth login
set -a
source .env
set +a
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com --project "$GCP_PROJECT_ID"
bash deploy.sh
```

`deploy.sh` uses Cloud Run source deployment: Cloud Build builds this Dockerfile,
Artifact Registry stores the image, and Cloud Run runs it. The account/build service
account must have the permissions required for source deployment in your project.
The script reads credentials from exported environment variables; never run it with
shell tracing (`set -x`). Do not commit `.env` or paste credential-bearing commands.

Defaults: `us-west1`, service `csci599-a1`, one CPU, 1 GiB memory, one worker,
concurrency 1, minimum 0 / maximum 1 instances, 300-second request timeout,
and public access for grading. Concurrency 1 protects sequential session rollback.
The command prints the service URL; repeat the local checks against that URL.

SQLite history and filesystem changes last only for the lifetime of the Cloud Run
instance. They can disappear on replacement or scale-to-zero; this matches the
assignment's instance-lifetime memory requirement. No external database is configured.

Costs: NIM and Tavily depend on your account's free-tier limits/credits; Open-Meteo
is free for non-commercial use. Cloud Run, Cloud Build, and Artifact Registry may
incur charges. Minimum instances 0 reduces idle compute cost, but image storage and
build charges can remain. Monitor your GCP education credit and API usage.

Example `/chat` request:

```json
{"query":"What is the current temperature in Los Angeles? Include the units.","session_id":"weather-test"}
```
