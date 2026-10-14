# Coding Agent to Langgraph Distillation

In [Module 1](../01_claude_code/README.md), Claude Code selected aspirin and five similar molecules, calculated their QED on Aurora with RDKit, and ranked them.
Here we do the following:

1. Distill the previous sequence into a reproducible Langgraph example
2. Use Model Access Gateway as the LLM provider.

## Before you start

Add these values to `settings.env` in the repository root:

```
LLM_MODEL=grok-4-1-fast-reasoning
OPENAI_BASE_URL=https://mag.genesis.americansciencecloud.org/v1
AMSC_TOKEN=<your MAG key>
```

To obtain a MAG key, follow [MAG get started](https://amsc-docs-d762d2.gitlab.io/mag-get-started).

`LLM_MODEL` must name a model with tool-calling support. `gpt-6-luna` answers plain
chat requests but returns a `401` on tool calls, so the graph below fails at the
`run_on_aurora` step.

## Prompt

Start Claude Code in the repository root. Then give this prompt:

```
Convert the Module 1 similar-molecules task into a LangGraph agent in intermediate/02_langgraph/similar_molecules.py: an LLM on the MAG proposes the molecules, I approve y/n, Globus Compute calculates QED on Aurora, and the LLM explains the ranking.
```

> **A finished `similar_molecules.py` already ships in this directory.** It is the
> author's reference version, not something your agent produced. The prompt above asks
> your agent to write that same file, so following it literally overwrites the
> reference. Pick one before you start:
>
> - **Run the reference** to see the module work, and skip the prompt.
> - **Write your own** to a different name, for example `similar_molecules_mine.py`,
>   and keep the reference to compare against.
> - **Overwrite it** as the prompt says. `git checkout intermediate/02_langgraph/similar_molecules.py`
>   restores the reference afterwards.
>
> `similar_molecules_local.py` is the same graph with the QED step on your own computer,
> useful if your endpoint is not ready.

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
