# Required Capabilities: Skills, Plugins, Connectors, MCP

This lists what the building agent (Claude Code) and the surrounding Hermes environment need to design, build, test, and deploy **Kaun Banega CHRO (KBC)**. Items are marked REQUIRED or OPTIONAL. The game runtime itself needs no external connector or MCP; those listed are for build tooling and deployment only.

## 1. Skills

| Skill | Where | Required? | Why |
|-------|-------|-----------|-----|
| `autonomous-ai-agents/claude-code` | Hermes | REQUIRED | The build is driven by the Claude Code agent using `CLAUDE_CODE_PROMPT.md`. This is the mechanism to launch it. |
| `software-development/test-driven-development` | Hermes | REQUIRED (recommended) | The PRD mandates `pytest` on `core/`. Loading TDD keeps the engine tested before the UI exists. |
| `creative/popular-web-designs` (or `claude-design`) | Hermes | OPTIONAL | Reference for the blue/teal/gold KBC visual language and clean corporate styling. Not needed if you are comfortable styling Streamlit directly. |
| `github/*` (e.g. `github-repo-management`, `github-pr-workflow`) | Hermes | OPTIONAL | Only if the game is to be version-controlled or turned into a PR. Not needed for a local build. |

Note: Claude Code's own sub-skills (Python, pytest, Docker) are assumed available in its environment; do not list them separately here.

## 2. Plugins

| Plugin | Required? | Why |
|--------|-----------|-----|
| None required for the game core or the Streamlit adapter. | - | The core uses only the Python standard library; Streamlit is a pip dependency. |
| Google Cloud CLI (`gcloud`) plugin/tooling | OPTIONAL | Needed only at deploy time to push the container to Cloud Run / Vertex. Can be run manually instead of via a plugin. |

## 3. Connectors

| Connector | Required? | Why |
|-----------|-----------|-----|
| None at runtime. | - | The game is fully offline: local `question_bank.json`, in-memory game state. No database, no API. |
| Google Cloud / Vertex AI connector | OPTIONAL | Used only to deploy `ui/vertex_app.py` to Cloud Run. Not used by the game while playing. |

## 4. MCP Servers

| MCP Server | Required? | Why |
|------------|-----------|-----|
| Filesystem MCP | OPTIONAL (recommended for agent) | Lets the building agent read/write `question_bank.json`, game state, and project files reliably across sessions. |
| Google Cloud MCP | OPTIONAL | Convenience for deploying to Cloud Run/Vertex from the agent. A manual `gcloud` run is an equally valid substitute. |
| Browser / Desktop MCP | OPTIONAL | Only useful if you want the agent to visually self-test the Streamlit UI. Not required; `pytest` plus a local `streamlit run` covers verification. |

## 5. Summary for a minimal setup

To build and run locally you need only:
- The `claude-code` skill (to run the prompt), or you can run the prompt in a Claude Code session manually.
- Python 3.11+, `streamlit`, `pytest` (in `requirements.txt`).
- The files already in `KBC_game/`: `PRD.md`, `question_bank.json`, `CLAUDE_CODE_PROMPT.md`.

To also deploy to Vertex/Cloud Run you additionally need:
- `gcloud` CLI authenticated to a GCP project.
- The `Dockerfile` produced by the build.
- (Optional) Google Cloud MCP for in-agent deploy.

No runtime connector or MCP is required for the game to function.
