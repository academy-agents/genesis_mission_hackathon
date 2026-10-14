# genesis_mission_hackathon
Material for Genesis Mission Hackathon Oct 2026

## Installation

### 1. Install uv

[uv](https://docs.astral.sh/uv/) manages Python and the dependencies for this repo.

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your shell, then verify the install:

```bash
uv --version
```

### 2. Install this repo

```bash
git clone https://github.com/academy-agents/genesis_mission_hackathon.git
cd genesis_mission_hackathon
uv sync
```

`uv sync` downloads Python 3.13 if necessary, creates a `.venv` directory, and installs the dependencies from `uv.lock`.

Copy the settings template, then fill in your endpoint IDs and `USER_AGENT_ID`:

```bash
cp settings.env.example settings.env
```

Git ignores `settings.env`, so your IDs stay local.

`settings.env` also holds the credentials for the LLM used from Module 2 onwards:

| Setting | Where it comes from |
|---|---|
| `AMSC_TOKEN` | Your Model Access Gateway (MAG) key. Follow [MAG get started](https://amsc-docs-d762d2.gitlab.io/mag-get-started) to obtain one. |
| `OPENAI_BASE_URL` | The MAG endpoint. The template ships the correct value; do not point it at a model provider's own API, or your MAG key is rejected with a misleading `401`. |
| `LLM_MODEL` | The template default supports tool calling, which Modules 2 and 3 require. |
| `USER_AGENT_ID` | From [dashboard.academy-agents.org](https://dashboard.academy-agents.org). Modules 3 and 4 fail with `KeyError` if it is empty. |

Use `uv run` to run scripts in this environment:

```bash
uv run python intermediate/00_endpoint_setup/remote_function_call.py
```

Or activate the environment:

```bash
source .venv/bin/activate
```
