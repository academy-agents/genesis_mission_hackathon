# Module 2: A coding agent that calls HPC tools

In [Module 1](../1_tool_calling/), you wrote the agent loop with LangChain and gave the LLM three Python functions as tools.
Here, you use a coding agent that has the loop and the tools already. The agent is [Pi](https://pi.dev) with the [Globus Harness](https://github.com/GusEllerm/pi-lab-profile) profile, and it runs in a Docker container. The agent has two types of tools:

- **Built-in tools:** read, write, edit, bash, grep, find, and ls. They operate on the files in the container.
- **MCP tools from [hpc-bridge](https://github.com/globus-labs/hpc-bridge):** connect to an HPC facility, start a compute block, run commands on it, and stop it.

You do not write code. You give the agent a task, and the agent selects the tools.

## What is in the image

| Part | Function |
|---|---|
| Pi (`@earendil-works/pi-coding-agent`) | The coding agent |
| Globus Harness, `lab` profile | A status column, `/endpoints`, a spend gate for HPC, and the ALCF inference gateway models |
| uv | Runs the hpc-bridge MCP server |
| git, ripgrep, OpenSSH client | Tools for the agent and for hpc-bridge |
| This repository | A copy in `/workspace/genesis_mission_hackathon`, where Pi starts |

## 1. Build and start

Install Docker. On macOS and Windows, use Docker Desktop. Then, from the repository root:

```bash
docker build -t gm-agent advanced/2_agent_tool_calling
docker run -it --name gm-agent gm-agent
```

## 2. Log in to a model

In Pi, type `/login`. Select a provider, for example Anthropic, and paste your API key. Then type `/model` and select a model.

> **Note:** The `globus/…` model in the profile needs the Globus Labs cluster. Select a different model.

To use the ALCF inference gateway, you need an ALCF account. In a second terminal, log in:

```bash
docker exec -it gm-agent uvx --from "alcf-ai==0.10.0" alcf-ai auth login
```

Then type `/model` in Pi and select an `alcf-…` model.

## 3. Give the agent a task

Type these in Pi:

| Input | Result |
|---|---|
| `/mcp` | Shows the `hpc` server and its tools. |
| `What HPC facilities can I use?` | The agent calls hpc-bridge and shows the facilities. |
| `Connect to Aurora and show the hostname of the login node.` | The agent connects to Aurora and runs `hostname` on the login node. |

If the system needs a password or a one-time passcode, the agent gives you an `ssh` command. Run the command inside the container, in a second terminal:

```bash
docker exec -it gm-agent <the ssh command from the agent>
```

> **Note:** Do not run the `ssh` command on your computer. hpc-bridge uses the SSH connection that you open in the container.

A compute block uses your allocation. The agent starts a compute block only after you confirm a dialog. When you are done, tell the agent to stop the endpoint. To see the facility, the block, and the node-hours, type `/hpc`.

## Start again later

When you exit Pi, the container stops. Your login and settings stay in the container. To start Pi again:

```bash
docker start -ai gm-agent
```

After you rebuild the image, remove the old container, then do `docker run` again:

```bash
docker rm gm-agent
```

**Challenge:** Tell the agent to do the [intermediate Module 1](../../intermediate/01_claude_code/README.md) task: calculate QED with RDKit on Aurora for aspirin and five similar molecules. Compare the result with the Claude Code result.
