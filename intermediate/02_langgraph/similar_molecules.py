"""Propose analogs of a molecule, confirm, compute QED on Aurora, and explain the ranking.

START -> propose -> confirm --yes--> run_on_aurora -> summarize -> END
                           \\--no--> END
"""

from __future__ import annotations

import os
import sys
import uuid
from dataclasses import dataclass, field

import dotenv
from globus_compute_sdk import Executor
from globus_compute_sdk.serialize import AllCodeStrategies, ComputeSerializer
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
    """Run on the remote endpoint. Put all imports inside the function."""
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
    # Aurora is a shared system: pause the graph until a human approves the submission.
    answer = interrupt({"endpoint": "Aurora", "molecules": state.molecules})
    return {"approved": str(answer).strip().lower() in ("y", "yes")}


def route_after_confirm(state: MoleculeState) -> str:
    return "run_on_aurora" if state.approved else END


def run_on_aurora(state: MoleculeState) -> dict:
    # Run on an Aurora compute node, in a batch job charged to the account
    config = {
        "account": os.environ["AURORA_ACCOUNT"],
        # hpc-bridge reads the PBS queue from "partition"
        "partition": os.environ["AURORA_QUEUE"],
        # Aurora holds jobs that do not name the file systems they use
        "scheduler_options": "#PBS -l filesystems=home:flare",
    }
    # To run on Perlmutter instead, use PERLMUTTER_ENDPOINT_ID below and this config
    # config = {
    #    "account": os.environ["PERLMUTTER_ACCOUNT"],
    #    "partition": "debug",
    #    # Perlmutter rejects jobs that do not select CPU or GPU nodes
    #    "scheduler_options": f"#SBATCH --constraint=cpu\n#SBATCH --reservation={os.environ['PERLMUTTER_RESERVATION']}",
    # }
    # To run on this computer instead, replace the with block below with
    # from concurrent.futures import ProcessPoolExecutor
    with Executor(
        endpoint_id=os.environ["AURORA_ENDPOINT_ID"], user_endpoint_config=config
    ) as ex:
        # Send compute_qed as code, so Aurora does not need this module to be importable.
        ex.serializer = ComputeSerializer(strategy_code=AllCodeStrategies())
        # The batch job can wait in the queue for several minutes
        rows = ex.submit(compute_qed, state.molecules).result(timeout=1200)
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
    builder.add_node("run_on_aurora", run_on_aurora)
    builder.add_node("summarize", summarize)

    builder.add_edge(START, "propose")
    builder.add_edge("propose", "confirm")
    builder.add_conditional_edges(
        "confirm", route_after_confirm, ["run_on_aurora", END]
    )
    builder.add_edge("run_on_aurora", "summarize")
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
