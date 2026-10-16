# Module 1: Claude Code with Globus Compute

This module has a Claude Code skill, `globus-compute-run`. The skill shows Claude Code how to run Python functions and shell commands on remote endpoints with Globus Compute.

## Start Claude Code

Start Claude Code in the repository root. The skill is in `.claude/skills/globus-compute-run/` and loads at startup.

```bash
claude
```

To make sure that the skill is loaded, type `/skills`. The list must show `globus-compute-run`.

## Example prompts

- `Use the tutorial endpoint to calculate the first 20 prime numbers in Python.`
- `Run "python3 --version" on the tutorial endpoint and show me the output.`

## Example: An agent uses a chemistry tool on Aurora

An agent is only as useful as its tools. In this example, Claude Code uses RDKit on Aurora as a tool.

Prompt:

```
On Aurora, use RDKit to calculate the QED drug-likeness of aspirin, CC(=O)Oc1ccccc1C(=O)O.
```

The agent:

1. Writes a shell command that runs Python with RDKit. `uv run --with rdkit` gets RDKit, so you do not install it on Aurora.
2. Sends the command to the Aurora endpoint with Globus Compute.
3. On Aurora, RDKit reads the SMILES string (`Chem.MolFromSmiles`) and calculates QED (`QED.qed`). QED is a score from 0 to 1. A high score means that the molecule is similar to known oral drugs.
4. Shows the result: `QED = 0.550`.

The agent in Module 2 uses the same QED calculation as its tool.

## Example: The agent selects molecules and the tool scores them

In the first example, you give the molecule. In this example, the agent selects the molecules. The tool calculates the scores.

Prompt:

```
On Aurora, use RDKit to calculate QED for aspirin and five similar molecules that you choose. Rank them and explain which change improved drug-likeness the most.
```

The agent:

1. Selects five molecules that are related to aspirin, and writes their SMILES strings.
2. Sends one command to Aurora. The command calculates QED for each molecule.
3. Ranks the results and explains them.

Result on Aurora:

| Molecule | SMILES | QED |
|---|---|---|
| ibuprofen | `CC(C)Cc1ccc(cc1)C(C)C(=O)O` | 0.822 |
| methyl salicylate | `COC(=O)c1ccccc1O` | 0.614 |
| salicylic acid | `OC(=O)c1ccccc1O` | 0.610 |
| paracetamol | `CC(=O)Nc1ccc(O)cc1` | 0.595 |
| salicylamide | `NC(=O)c1ccccc1O` | 0.591 |
| aspirin | `CC(=O)Oc1ccccc1C(=O)O` | 0.550 |

Ibuprofen has the highest score, but it is a different molecule, not a small change to aspirin. In the aspirin family, the best change is to remove the acetyl ester (salicylic acid, 0.610) or to replace the acid with a methyl ester (methyl salicylate, 0.614).

The agent selects molecules, the tool scores them, and the agent makes a conclusion. Module 2 does these steps again and again in a loop with LangGraph.

To use your own endpoint, first do the steps in [Module 0](../00_endpoint_setup/README.md).
