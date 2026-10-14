# Coding Agent to Langgraph Distillation

In [Module 1](../01_claude_code/README.md), Claude Code selected aspirin and five similar molecules, calculated their QED on Aurora with RDKit, and ranked them.
Here we do the following:

1. Distill the previous sequence into a reproducible Langgraph example
2. Use Model Access Gateway as the LLM provider.

## Before you start

Add these values to `settings.env` in the repository root:

```
LLM_MODEL=gpt-6-luna
OPENAI_BASE_URL=https://mag.genesis.americansciencecloud.org/v1
AMSC_TOKEN=<your MAG key>
```

## Prompt

Start Claude Code in the repository root. Then give this prompt:

```
Convert the Module 1 similar-molecules task into a LangGraph agent in intermediate/02_langgraph/similar_molecules.py: an LLM on the MAG proposes the molecules, I approve y/n, Globus Compute calculates QED on Aurora, and the LLM explains the ranking.
```

The `langgraph-mag-agent` skill gives Claude Code the MAG settings, the approval step, and the Globus Compute rules.

The agent makes this graph:

```
START -> propose -> confirm --y--> run_on_aurora -> summarize -> END
                            \--n--> END
```

## Run the agent

```bash
uv run python intermediate/02_langgraph/similar_molecules.py
```

The agent shows the molecules and asks `[y/N]` before it sends work to Aurora.

## Run without Aurora

`similar_molecules_local.py` is the same agent, but it calculates QED on your computer. You do not need an endpoint. The LLM is still on the MAG.

```bash
uv run python intermediate/02_langgraph/similar_molecules_local.py
```
