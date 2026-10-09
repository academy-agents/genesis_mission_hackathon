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

Use `uv run` to run scripts in this environment:

```bash
uv run python intermediate/00_endpoint_setup/remote_function_call.py
```

Or activate the environment:

```bash
source .venv/bin/activate
```
