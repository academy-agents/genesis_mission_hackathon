# Module 0: Globus Compute endpoint setup

A Globus Compute endpoint runs your Python functions on a remote system, for example Aurora, Perlmutter, or Frontier.

You can set up the endpoint in two ways:

- **hpc-bridge plugin:** **[Recommended]** Uses Claude code (and others) to connect to HPC systems.
- **Manual setup:** Log in to the system and follow steps.

> **Note:** The `globus-compute-endpoint` package is installed when you install 
> this repo with `uv sync`. Refer to the [top-level README](../../README.md). 
> For the manual setup, do the steps below on the system where the endpoint 
> must run, for example a login node.

## 1. Install the plugin (user)

When you start Claude Code in this repository and trust the folder, it offers to install hpc-bridge (from `.claude/settings.json`). If it does not, type these commands in Claude Code. An agent cannot run slash commands:

```
/plugin marketplace add globus-labs/hpc-bridge
/plugin install hpc-bridge@hpc-bridge
/reload-plugins
```

Then give the agent one prompt, for example:

```
Connect to aurora.alcf.anl.gov, install genesis_mission_hackathon, and start a globus_compute_endpoint configured to provision compute nodes
```

The agent connects to the system, installs this repo, starts the endpoint, and adds the endpoint UUID to `settings.env`.

>  If the system needs a password or a one-time passcode, the agent gives you an `ssh` command. Copy the command and paste it into your own terminal, not into Claude Code, and log in there.

When the agent is done, do [step 4](#4-test-the-endpoint) to test the endpoint.

# Manual Configuration
### 1. Configure the endpoint

```bash
uv run globus-compute-endpoint configure gm_endpoint
```

This command creates the endpoint configuration in `~/.globus_compute/gm_endpoint/`.

### 2. Start the endpoint

```bash
uv run globus-compute-endpoint start gm_endpoint
```

The first time, the command shows a Globus login link. Open the link and log in.

When the endpoint starts, it shows its endpoint UUID. To show the UUID again, use:

```bash
uv run globus-compute-endpoint list
```

### 3. Add the endpoint UUID to settings.env

Copy the endpoint UUID into `settings.env` in the project root. Use the variable for your system:

```
AURORA_ENDPOINT_ID=<your-endpoint-uuid>
PERLMUTTER_ENDPOINT_ID=<your-endpoint-uuid>
FRONTIER_ENDPOINT_ID=<your-endpoint-uuid>
```

### 4. Test the endpoint

```bash
uv run python intermediate/00_endpoint_setup/remote_function_call.py
```

The script runs `hello_world` on each endpoint in `settings.env` and shows the result.

# Run tasks on compute nodes

The endpoint that hpc-bridge makes (`hpc-bridge-<site>`) can run a task on the login node or on a compute node. If the task sends `"compute": True` in `user_endpoint_config`, the endpoint submits a batch job: a PBS job on Aurora, or a Slurm job on Perlmutter.

1. In `settings.env`, set `AURORA_COMPUTE_ENDPOINT_ID` and `PERLMUTTER_COMPUTE_ENDPOINT_ID` to the hpc-bridge endpoint IDs. Set `AURORA_ACCOUNT` and `PERLMUTTER_ACCOUNT` to your allocations.
2. Run the test:

   ```bash
   uv run python intermediate/00_endpoint_setup/remote_compute_node_call.py
   ```

The script submits one 10 minute `debug` job on each system. It waits for the job to start, then shows the host name of the compute node. The job uses your allocation.

# HPC-Bridge

[hpc-bridge](https://github.com/globus-labs/hpc-bridge) lets a coding agent do the steps above for you. It is a Claude Code plugin. It is also a standard MCP server, so you can use it with other coding agents, for example Cursor or the OpenAI Agents SDK. For other coding agents, refer to [other MCP hosts](https://github.com/globus-labs/hpc-bridge/blob/main/docs/user/other-hosts.md).

## Notes for coding agents

- The user must do the steps that have the label **(user)**. Give the user the exact command to run.
- Do not ask for, type, or show a password or a PIN. Do not show the contents of `settings.env`. It contains `USER_AGENT_ID`.
- Run all remote commands on the login node with `run_shell(shape="login")`. Do not start a compute block. This setup does not use the allocation.

