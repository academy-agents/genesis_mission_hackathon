# Intermediate Track: Agentic science workflows

Presenter: Yadu Babuji

Each module uses the result of the previous module. Install the repo first with the [top-level README](../README.md).

- [Module 0: Globus Compute endpoint setup](00_endpoint_setup/README.md). Start a Globus Compute endpoint on Aurora, Perlmutter, or Frontier, with a coding agent and hpc-bridge or by hand. The other modules send their tasks to this endpoint.
- [Module 1: Claude Code with Globus Compute](01_claude_code/README.md). Claude Code uses a skill to run RDKit on Aurora and calculate the QED drug-likeness of molecules. You give prompts. You do not write code.
- [Module 2: LangGraph workflow](02_langgraph/README.md). Change the Module 1 session into a LangGraph agent that you can run again. An LLM on the Model Access Gateway (MAG) proposes molecules, you approve them, and Aurora calculates QED.
- [Module 3: Many agents with Academy](03_academy/README.md). Academy starts several agents on Aurora. Each agent runs a LangGraph loop to find molecules with a higher QED.
- [Module 4: Academy Dashboard](04_dashboard/README.md). Monitor your agents on a web dashboard. See their logs and answer their questions, and find where they run on a map.

# Advanced Track: Scaling Multi-Agent Workflows

Presented: Kyle Chard

- [Module 1: Tool calling with Globus Compute](../advanced/1_tool_calling/README.md). An LLM on the MAG calls Python tools, for example a prime count or a molecular energy. A wrapper sends each tool call to a remote endpoint with Globus Compute.
- [Module 2: Agent tool calling](../advanced/2_agent_tool_calling/README.md). A coding agent, Pi with the Globus Harness profile, runs in a Docker container. It uses its built-in tools and the hpc-bridge MCP tools to do work on an HPC system.
- [Module 3: Scaling agents with Academy](../advanced/3_scaling_agents/README.md). Many Claude Agent SDK agents play Wordle as Academy agents. The three scripts go from independent agents (`1_independent.py`), to agents that share hints on a blackboard (`2_message_board.py`), to a coordinator that sends strategies to worker agents (`3_multi_strategy.py`).


# Getting Started

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). uv manages Python and the dependencies for this repo.

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone this repo and install it:

   ```bash
   git clone https://github.com/academy-agents/genesis_mission_hackathon.git
   cd genesis_mission_hackathon
   uv sync
   ```

3. Copy the settings template. Then add your endpoint IDs, your `USER_AGENT_ID` from
   [dashboard.academy-agents.org](https://dashboard.academy-agents.org), and your MAG
   key from [MAG get started](https://amsc-docs-d762d2.gitlab.io/mag-get-started):

   ```bash
   cp settings.env.example settings.env
   ```

4. Run scripts with `uv run`, for example 

   ```bash
   uv run python intermediate/00_endpoint_setup/remote_function_call.py
   ```

For Windows and more details, refer to the [top-level README](../README.md).
