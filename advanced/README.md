# Advanced modules

In the intermediate modules, an agent used a tool on an HPC system, ran in a LangGraph loop, and then ran as many copies on Aurora with Academy.

In the advanced modules, you build these parts yourself:

| Module | Pattern | What you learn |
|---|---|---|
| [1. Tool calling](1_tool_calling/) | An LLM selects which HPC function to run | How to make a Globus Compute function into an LLM tool |
| [2. Agent tool calling](2_agent_tool_calling/) | A coding agent calls HPC tools | How a ready-made agent uses its built-in tools and the hpc-bridge MCP tools |
| [3. Scaling agents](3_scaling_agents/) | Many LLM agents work on one problem | Three ways to organize agents: independent, peers, and coordinator with sub-agents |

## Before you start

1. Install this repo. Refer to the [top-level README](../README.md).
2. For Module 1, you need a Globus Compute endpoint. Refer to [intermediate Module 0](../intermediate/00_endpoint_setup/README.md).
3. For Module 2, install Docker.
4. Get your AmSC token for the Model Access Gateway (MAG). Refer to [MAG get started](https://amsc-docs-d762d2.gitlab.io/mag-get-started). Then put the token in your shell:

   ```bash
   export AMSC_TOKEN=<your MAG key>
   ```

Modules 1 and 3 use an LLM on the MAG. The MAG has two interfaces, and each module uses one of them:

| Interface | Used by | Environment variables |
|---|---|---|
| OpenAI-compatible | Module 1 (LangChain `ChatOpenAI`) | `OPENAI_API_KEY=$AMSC_TOKEN`<br>`OPENAI_BASE_URL=https://mag.genesis.americansciencecloud.org/v1` |
| Anthropic-compatible | Module 3 (Claude Agent SDK) | `ANTHROPIC_AUTH_TOKEN=$AMSC_TOKEN`<br>`ANTHROPIC_BASE_URL=https://mag.genesis.americansciencecloud.org` |

> **Note:** The Anthropic base URL does not end in `/v1`. The OpenAI base URL does.

To show the models that you can use:

```bash
source utilities/mag_shell_util.sh
mag --list
```

## 1. Tool calling

The decorator `gce_wrapper` sends each function call to Globus Compute and waits for the result. The LLM sees a usual Python function with a name, a docstring, and type hints. The LLM does not know that the function runs on an HPC system.

| File | What it does |
|---|---|
| `test_globus_compute.py` | Runs `hello_world` on the endpoint. Run this file first to test the endpoint. |
| `tool_calling_globus_compute.py` | Gives an LLM three tools: count primes, calculate molecular energy, and run an MD trajectory. The script asks one random question, and the LLM selects the tool to run. |

> **Note:** `compute_energy` and `compute_trajectory` return mock values. To make real tools, replace them with real code, for example PySCF or OpenMM.

Before you run the scripts, change `compute_endpoint` in both files to your endpoint UUID from `settings.env`. Remove `user_endpoint_config`. It contains the account and queue for the example Polaris endpoint.

```bash
export OPENAI_API_KEY=$AMSC_TOKEN
export OPENAI_BASE_URL=https://mag.genesis.americansciencecloud.org/v1
uv run python advanced/1_tool_calling/test_globus_compute.py
uv run python advanced/1_tool_calling/tool_calling_globus_compute.py
```

The script uses the model `gpt-oss-120b`. To use a different model, change `model` in `ChatOpenAI`.

**Challenge:** Add a tool that calculates QED with RDKit, as in [intermediate Module 1](../intermediate/01_claude_code/README.md). Ask the LLM about the drug-likeness of aspirin.

## 2. Agent tool calling

In Module 1, you write the agent loop. In Module 2, a coding agent has the loop already. [Pi](https://pi.dev) with the [Globus Harness](https://github.com/GusEllerm/pi-lab-profile) profile runs in a Docker container. The agent uses its built-in tools (read, edit, bash) and the [hpc-bridge](https://github.com/globus-labs/hpc-bridge) MCP tools to do work on an HPC system.

From the repository root:

```bash
docker build -t gm-agent advanced/2_agent_tool_calling
docker run -it --name gm-agent gm-agent
```

In Pi, type `/login` to add your API key. For the other model options and how to connect to an HPC system, refer to the [Module 2 README](2_agent_tool_calling/README.md).

## 3. Scaling agents

Each script runs Wordle agents. The agents use the Claude Agent SDK, and Academy runs them. Wordle is a small model of an expensive simulation: each guess is one evaluation, and the feedback tells the agent how near it is to the answer.

| Script | Pattern | Agents |
|---|---|---|
| `1_independent.py` | **Independent.** Each agent plays alone. | 2 `WordleAgent` |
| `2_message_board.py` | **Peers.** The agents share what they learn on a blackboard. | 2 `WordleAgent` |
| `3_multi_strategy.py` | **Coordinator and sub-agents.** The sub-agents test strategies on a cheap simulator. Then the coordinator plays the real game one time with the best strategy. | 1 `CoordinatorAgent` and 3 `StrategyAgent` |

```bash
export ANTHROPIC_AUTH_TOKEN=$AMSC_TOKEN
export ANTHROPIC_BASE_URL=https://mag.genesis.americansciencecloud.org
uv run python advanced/3_scaling_agents/1_independent.py
```

`uv sync` installs the Claude Agent SDK. The SDK includes the Claude Code CLI, so you do not install the CLI.

At the end, each script shows the answer from each agent and the true target word.

These scripts use `LocalExchangeFactory`, so all agents run in one process on your computer. To run agents on an HPC system, use `HttpExchangeFactory` and a Globus Compute executor, as in [intermediate Module 3](../intermediate/03_academy/README.md).

**Challenge:** In `2_message_board.py`, change `range(2)` to `range(4)`. Do more peers find the word in fewer guesses?
