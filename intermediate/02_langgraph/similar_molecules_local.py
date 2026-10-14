"""Propose analogs of a molecule, confirm, compute QED on this computer, and explain the ranking.

START -> propose -> confirm --yes--> run_locally -> summarize -> END
                           \\--no--> END
"""

from __future__ import annotations

import os
import sys
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import dotenv
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel
from rdkit import Chem

dotenv.load_dotenv(dotenv.find_dotenv("settings.env", usecwd=True))

DEFAULT_REQUEST = (
    "Calculate QED for aspirin and five similar molecules that you choose. "
    "Rank them and explain which change improved drug-likeness the most."
)


class Molecule(BaseModel):
    name: str
    smiles: str


class Proposal(BaseModel):
    """The parent molecule first, followed by the proposed analogs."""

    molecules: list[Molecule]


@dataclass
class MoleculeState:
    request: str
    molecules: dict[str, str] = field(default_factory=dict)
    approved: bool = False
    results: list[dict] = field(default_factory=list)
    summary: str = ""


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ["LLM_MODEL"],
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["AMSC_TOKEN"],
        # The hackathon project only has a microsoft allocation on MAG.
        default_headers={"X-AmSC-MAG-Provider": "microsoft"},
    )


def compute_qed(molecules: dict) -> list[dict]:
    """Run in a worker process. Put all imports inside the function."""
    import platform

    from rdkit import Chem
    from rdkit.Chem import QED

    rows = []
    for name, smiles in molecules.items():
        mol = Chem.MolFromSmiles(smiles)
        props = QED.properties(mol)
        rows.append(
            {
                "name": name,
                "smiles": smiles,
                "qed": round(QED.qed(mol), 3),
                "mw": round(props.MW, 1),
                "alogp": round(props.ALOGP, 2),
                "hba": props.HBA,
                "hbd": props.HBD,
                "psa": round(props.PSA, 1),
                "rotb": props.ROTB,
                "arom": props.AROM,
                "alerts": props.ALERTS,
                "host": platform.node(),
            }
        )
    return rows


def propose(state: MoleculeState) -> dict:
    llm = get_llm().with_structured_output(Proposal, method="json_schema")
    proposal = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert medicinal chemist. Return the parent molecule named in the "
                    "request first, then the requested number of close analogs. Make each analog "
                    "differ from the parent by one clear structural change. Use valid SMILES."
                )
            ),
            HumanMessage(content=state.request),
        ]
    )
    molecules = {
        m.name: m.smiles for m in proposal.molecules if Chem.MolFromSmiles(m.smiles)
    }
    return {"molecules": molecules}


def confirm(state: MoleculeState) -> dict:
    # Pause the graph until a human approves the run.
    answer = interrupt({"endpoint": "this computer", "molecules": state.molecules})
    return {"approved": str(answer).strip().lower() in ("y", "yes")}


def route_after_confirm(state: MoleculeState) -> str:
    return "run_locally" if state.approved else END


def run_locally(state: MoleculeState) -> dict:
    # Run compute_qed in a separate process on this computer
    with ProcessPoolExecutor() as ex:
        rows = ex.submit(compute_qed, state.molecules).result(timeout=300)
    return {"results": sorted(rows, key=lambda r: r["qed"], reverse=True)}


def summarize(state: MoleculeState) -> dict:
    table = "\n".join(
        str({k: v for k, v in r.items() if k != "host"}) for r in state.results
    )
    response = get_llm().invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert medicinal chemist. Using only the QED results and property "
                    "breakdowns given, rank the molecules and explain which structural change from "
                    "the parent improved drug-likeness the most, citing the properties that moved. "
                    "Be concise."
                )
            ),
            HumanMessage(
                content=f"Request: {state.request}\n\nResults (best first):\n{table}"
            ),
        ]
    )
    return {"summary": response.content}


def build_graph():
    builder = StateGraph(MoleculeState)
    builder.add_node("propose", propose)
    builder.add_node("confirm", confirm)
    builder.add_node("run_locally", run_locally)
    builder.add_node("summarize", summarize)

    builder.add_edge(START, "propose")
    builder.add_edge("propose", "confirm")
    builder.add_conditional_edges("confirm", route_after_confirm, ["run_locally", END])
    builder.add_edge("run_locally", "summarize")
    builder.add_edge("summarize", END)
    # The checkpointer saves state at the interrupt so the graph can resume after input().
    return builder.compile(checkpointer=InMemorySaver())


def main() -> int:
    request = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REQUEST
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    state = graph.invoke(MoleculeState(request=request), config)
    while "__interrupt__" in state:
        payload = state["__interrupt__"][0].value
        print(f"Submit these molecules to {payload['endpoint']}?")
        for name, smiles in payload["molecules"].items():
            print(f"  {name:<28}{smiles}")
        state = graph.invoke(Command(resume=input("[y/N] ")), config)

    if not state["approved"]:
        print("Not submitted.")
        return 0

    print(f"\nRan on {state['results'][0]['host']}")
    print(f"{'rank':<5}{'name':<28}{'QED':>6}{'MW':>8}{'ALogP':>7}{'Alerts':>8}")
    for i, r in enumerate(state["results"], 1):
        print(
            f"{i:<5}{r['name']:<28}{r['qed']:>6.3f}{r['mw']:>8.1f}{r['alogp']:>7.2f}{r['alerts']:>8}"
        )
    print(f"\n{state['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
