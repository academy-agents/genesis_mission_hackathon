# From a coding agent session to a reproducible LangGraph workflow

In [Module 1](../01_claude_code/README.md), Claude Code selected aspirin and five similar molecules, calculated their QED on Aurora with RDKit, and ranked them.
Here we do the following:

1. Rewrite that one-off session as a standalone program you can run again
2. Use the Model Access Gateway (MAG) as the LLM provider

## What this module does

In Module 1 **Claude Code was the agent**: it chose the molecules, wrote the code, sent
it to Aurora, and interpreted the table. That only exists as a conversation. You cannot
re-run it tomorrow, schedule it, test it, or hand it to a colleague unchanged.

Here you write that same work as a Python program. The judgement Claude Code supplied
becomes an explicit LLM call, your implicit agreement becomes a literal `[y/N]` prompt,
and the Aurora submission becomes code. The result runs with `uv run python ...`, behaves
the same way each time, and does not need a coding agent at all.

**Nothing is deployed anywhere.** The program runs on your computer and exits.
[LangGraph](https://langchain-ai.github.io/langgraph/) is a framework for building such
workflows as a graph of named steps sharing a state object. It is used here for one
feature in particular: a checkpointer, which lets `interrupt()` stop the graph mid-run and
`Command(resume=...)` continue from the same place. That is what makes the approval step a
real pause rather than a cosmetic one.

Each step runs somewhere different:

| Step | Runs where |
|---|---|
| `propose` — choose the molecules | an LLM on the MAG, over HTTPS |
| `confirm` — approve or decline | your terminal |
| `run_on_aurora` — calculate QED | a batch job on an Aurora compute node, via Globus Compute |
| `summarize` — explain the ranking | an LLM on the MAG again |

The **Model Access Gateway (MAG)** is a proxy run by the American Science Cloud. Instead of
your own account with each model vendor, you use one MAG key and name the model you want;
the gateway forwards the request. That is why `OPENAI_BASE_URL` points at
`mag.genesis.americansciencecloud.org` rather than at a vendor's own API.

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
> `similar_molecules_local.py` is the same graph with one change: the QED calculation
> runs on your own computer instead of Aurora, so you do not need a Globus Compute
> endpoint. The `propose` and `summarize` steps still call the MAG exactly as before, so
> you still need your MAG key. Use it if your endpoint is not ready.

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

Answering `y` submits a batch job charged to your allocation, so it waits in the queue
for a few minutes before the results appear. Answering `n` ends the run without
submitting anything.
