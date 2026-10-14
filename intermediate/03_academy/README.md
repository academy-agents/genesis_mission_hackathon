# Module 3: Run many agents with Academy

In [Module 2](../02_langgraph/README.md), one LangGraph agent ran on your computer and sent one task to Aurora.
Here, Academy starts two `MolDesignAgent` agents, one for each seed molecule (aspirin and 5-methylhydantoin). Each agent runs its own LangGraph loop to find molecules with a high QED.

This module has two scripts:

| Script | Where the agents run | What you need |
|---|---|---|
| `local_discovery_campaign.py` | On your computer | MAG values in `settings.env` |
| `remote_discovery_campaign.py` | On Aurora, with Globus Compute | MAG values, and an Aurora endpoint |

Start with the local campaign.

## Before you start

Add the MAG values to `settings.env` in the repository root. This module uses `grok-4.1` as the LLM:

```
LLM_MODEL=grok-4.1
OPENAI_BASE_URL=https://mag.genesis.americansciencecloud.org/v1
AMSC_TOKEN=<your MAG key>
```

The MAG is available only from DOE laboratory networks.

## Run the agents on your computer

```bash
uv run python intermediate/03_academy/local_discovery_campaign.py
```

The agents run in threads on your computer, and they send messages through a local Academy exchange. The LLM is not on your computer: each agent sends its LLM requests to `grok-4.1` on the MAG. The LLM plans and selects the molecules. RDKit calculates QED on your computer.

The script:

1. Starts one `MolDesignAgent` for each seed molecule.
2. Each agent plans, asks the LLM for molecules, calculates QED with RDKit, and makes a conclusion. Then the loop starts again.
3. Every 30 seconds, the script asks each agent for a report. The report shows how many molecules the agent calculated, and the five best molecules.
4. After 4 reports, the script stops the agents.

To change the number of reports or the time between them, use `--rounds` and `--interval`:

```bash
uv run python intermediate/03_academy/local_discovery_campaign.py --rounds 2 --interval 60
```

## Run the agents on Aurora

`remote_discovery_campaign.py` starts the same agents on Aurora with Globus Compute. It uses the Academy cloud exchange.

Before you run it:

1. Do the steps in [Module 0](../00_endpoint_setup/README.md) for Aurora. The endpoint must run in the environment where this repo is installed, so that the workers can import `intermediate.custom_agents`.
2. On Aurora, get the latest code: `cd ~/genesis_mission_hackathon && git pull && uv sync`.
3. Add `AURORA_ACCOUNT=<your ALCF project>` to `settings.env`. Examine `user_endpoint_config` in the script (account, queue `debug`, walltime `00:10:00`). The endpoint template on Aurora must use these variables.

```bash
uv run python intermediate/03_academy/remote_discovery_campaign.py
```

The script sends `LLM_MODEL`, `OPENAI_BASE_URL`, and `AMSC_TOKEN` to the agents as arguments. You do not copy `settings.env` to Aurora. This script does not stop. To stop it, push Ctrl+C.

The agent code is in [`../custom_agents/mol_design_agents.py`](../custom_agents/mol_design_agents.py).

## Challenge

Add a third seed molecule to `seeds` in `local_discovery_campaign.py`. Compare the best QED of each agent.
