"""Full copy of MolDesignAgent that sends its logs and stats to the Academy Dashboard.

The differences from mol_design_agents.py:
- The base class is MonitoredAgent instead of Agent.
- __init__ takes user_agent_handle and calls super().__init__().
- agent_on_startup and agent_on_shutdown call super().
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
from academy.agent import action, loop
from academy.handle import Handle
from academy_dashboard import MonitoredAgent, UserAgent
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from rdkit import Chem
from rdkit.Chem import QED

logger = logging.getLogger(__name__)


def _compute_qed_sync(smiles: str) -> float:
    """Compute the QED (drug-likeness) score of a molecule."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Parse failure for {smiles}")
    return QED.qed(mol)


@dataclass
class SearchState:
    seed: str
    plan: str = ""
    tool_calls: list[Any] = field(default_factory=list)
    simulated_molecules: dict[str, float] = field(default_factory=dict)
    conclusions: list[str] = field(default_factory=list)
    critique: str = ""


class MonitoredMolDesignAgent(MonitoredAgent):
    """MolDesignAgent that sends its logs and stats to the Academy Dashboard."""

    def __init__(
        self,
        start_molecule: str,
        llm_model: str,
        base_url: str,
        api_key: str,
        user_agent_handle: Handle[UserAgent],
    ):
        super().__init__(user_agent_handle=user_agent_handle)
        self.llm_model = llm_model
        self.base_url = base_url
        self.api_key = api_key
        self.search_state = SearchState(seed=start_molecule)
        self.molecule_cache: dict[str, float] = {}

    async def agent_on_startup(self) -> None:
        # Start the log forwarding to the dashboard
        await super().agent_on_startup()
        n_workers: int
        if sys.platform == "darwin":  # pragma: no cover
            n_workers = 2
        else:
            n_workers = max(
                len(os.sched_getaffinity(0)) - 1,
                1,
            )  # Get cores we are assigned to
        self.pool = ProcessPoolExecutor(max_workers=n_workers)

        tools = [tool(self.compute_qed)]
        # Give each agent its own HTTP client. The default client is shared by the
        # whole process, so a second agent on the same worker would reuse
        # connections from a closed event loop ("Event loop is closed").
        self.http_client = httpx.AsyncClient()
        llm = ChatOpenAI(
            http_async_client=self.http_client,
            model=self.llm_model,
            base_url=self.base_url,
            api_key=self.api_key,
            # The hackathon project only has a microsoft allocation on MAG.
            default_headers={"X-AmSC-MAG-Provider": "microsoft"},
        )
        self.reasoning_llm = llm
        self.generation_llm = llm
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm_with_tools = self.generation_llm.bind_tools(tools)

    async def agent_on_shutdown(self) -> None:
        self.pool.shutdown()
        await self.http_client.aclose()
        await super().agent_on_shutdown()

    async def compute_qed(self, smiles: str) -> float:
        """Compute the QED (drug-likeness) score for the given molecule.

        Args:
            smiles: SMILES string to evaluate
        Returns:
            QED score from 0 to 1, higher is more drug-like
        """
        if smiles in self.molecule_cache:
            return self.molecule_cache[smiles]

        loop = asyncio.get_event_loop()
        qed = await loop.run_in_executor(
            self.pool,
            _compute_qed_sync,
            smiles,
        )
        self.molecule_cache[smiles] = qed
        return qed

    @loop
    async def conduct_simulation_campaign(
        self,
        shutdown: asyncio.Event,
    ) -> None:
        """Conduct a simulation campaign.

        This loop uses an LLM to conduct a search for molecules with high
        QED (drug-likeness), using the starting molecule as a seed for the
        search space.
        """

        async def plan(state: SearchState) -> SearchState:
            response = await self.reasoning_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a expert computational chemist tasked "
                            "with finding molecules with desired properties. "
                            "You should use simulations to explore the "
                            "chemical space in search of better molecules. "
                            "Come up with a plan for novel molecules to "
                            "simulate. Ground your proposed molecules in "
                            "knowledge of chemical and physical properties. "
                            "For each proposed molecule that you simulate, "
                            "provide the reasoning about why you expect this "
                            "molecule to be better either than previous "
                            "molecules that you have seen, or what you hope "
                            "to learn from running the simulation. In addition"
                            " to the target property, you should always "
                            "consider things like cost and sythesizability. "
                            "Note: the only experiment your lab is capable of "
                            "running is calculating the QED (drug-likeness) of "
                            "proposed molecules."
                        ),
                    ),
                    HumanMessage(
                        content=(
                            "Look for molecules with high QED "
                            f"starting with the molecule {state.seed}"
                        ),
                    ),
                ],
            )

            logger.info(f"Planner: {response}")

            return SearchState(
                seed=state.seed,
                plan=response.content,
                tool_calls=state.tool_calls,
                simulated_molecules=state.simulated_molecules,
                conclusions=state.conclusions,
                critique=state.critique,
            )

        async def tool_calling(state: SearchState) -> SearchState:
            previously_simulated = " ".join(
                state.simulated_molecules.keys(),
            )
            response = await self.llm_with_tools.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a computational chemist who is an expert "
                            "at conducting simulations. Using proposed plan "
                            "and chemical reasoning provided, decide which "
                            "simulations to run using the given tool. Do not "
                            "write python code. You should run several "
                            "simulations at once. Do not repeat previously "
                            "conducted simulations."
                        ),
                    ),
                    HumanMessage(
                        content=(
                            f"Plan: {state.plan}\n\n"
                            f"Simulated Molecules: {previously_simulated} "
                            "Do not repeat those molecules in the tool calls."
                        ),
                    ),
                ],
            )
            logger.info(f"Tool Calling: {response}")
            while len(response.tool_calls) == 0:
                logger.warning("Tool calling agent did not call tools!")
                logger.warning(response)
                response = await self.llm_with_tools.ainvoke(
                    [
                        SystemMessage(
                            content=(
                                "You are a computational chemist who is "
                                "an expert at conducting simulations. "
                                "sing proposed plan and chemical reasoning"
                                " provided, decide which simulations to run"
                                " using the given tool. Do not write python "
                                "code. You should run several simulations at "
                                "once. Do not repeat previously conducted "
                                "simulations."
                            ),
                        ),
                        HumanMessage(
                            content=(
                                f"Plan: {state.plan}\n\n"
                                f"Simulated Molecules: {previously_simulated}"
                                "Do not repeat those molecules in the tool "
                                "calls."
                            ),
                        ),
                        response,
                        HumanMessage(
                            content=(
                                "That response does not contain any correctly"
                                "formatted tool calls that could be parsed. "
                                "Please try again! Do not write python code!"
                            ),
                        ),
                    ],
                )

            return SearchState(
                seed=state.seed,
                plan=state.plan,
                tool_calls=response.tool_calls,
                simulated_molecules=state.simulated_molecules,
                conclusions=state.conclusions,
                critique=state.critique,
            )

        async def simulate(state: SearchState) -> SearchState:
            """Performs the tool call"""
            logger.info(
                f"Previous Simulations: {len(state.simulated_molecules)}",
            )
            logger.info(f"New Simulations: {len(state.tool_calls)}")
            if len(state.tool_calls) == 0:
                return state

            observations = []
            for tool_call in state.tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observations.append(
                    asyncio.create_task(tool.ainvoke(tool_call["args"])),
                )

            # gather keeps the order of the tool calls
            done = await asyncio.gather(*observations, return_exceptions=True)

            results = {}
            for tool_call, observation in zip(state.tool_calls, done, strict=True):
                if isinstance(observation, Exception):
                    observation = str(observation)
                results[tool_call["args"]["smiles"]] = observation

            new_results = state.simulated_molecules | results

            return SearchState(
                seed=state.seed,
                plan=state.plan,
                tool_calls=[],
                simulated_molecules=new_results,
                conclusions=state.conclusions,
                critique=state.critique,
            )

        async def conclude(state: SearchState) -> SearchState:
            results_str = "\n".join(
                f"{molecule}\t\t{energy}"
                for molecule, energy in state.simulated_molecules.items()
            )
            response = await self.generation_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are expert chemist analyzing the results"
                            "of simulations. Synthesize any conclusions from"
                            " the planned computational campaign and the "
                            "simulation results so far. An error result means "
                            "the simulation could not be run, likely because "
                            "the SMILES string of the molecule was invalid. "
                            "You should not repeat conclusions that have "
                            "already been reached but should correct the "
                            "conclusions if they are wrong. For each "
                            "conclusion, output a concise, stand-alone "
                            "statement. Return only the new conclusions."
                        ),
                    ),
                    HumanMessage(
                        content=(
                            f"Plan: {state.plan}\n\n"
                            "Simulation Results:\n"
                            "Molecule\t\tQED\n"
                            f"{results_str}"
                        ),
                    ),
                ],
            )
            logger.info(f"Conclusions: {response}")
            new_state = SearchState(
                seed=state.seed,
                plan=response.content,
                tool_calls=state.tool_calls,
                simulated_molecules=state.simulated_molecules,
                conclusions=[*state.conclusions, response.content],
                critique=state.critique,
            )
            self.search_state = new_state
            return new_state

        async def critique(state: SearchState) -> SearchState:
            results_str = "\n".join(
                f"{molecule}\t\t{energy}"
                for molecule, energy in state.simulated_molecules.items()
            )
            conclusions = "\n\t".join(state.conclusions)
            response = await self.generation_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are expert chemist analyzing the results of "
                            "simulations. Critique the planned simulation "
                            "campaign based on the chemistry foundations, "
                            "the computational results, and the conclusions "
                            "drawn. Be extremely critical. Look for flaws in "
                            "the methodology and reasoning."
                        ),
                    ),
                    HumanMessage(
                        content=(
                            f"Plan: {state.plan}\n\n"
                            "Simulation Results:\n"
                            "Molecule\t\tQED\n"
                            f"{results_str}\n\n"
                            "Conclusions:\n"
                            f"\t{conclusions}"
                        ),
                    ),
                ],
            )
            logger.info(f"Critique: {response}")
            return SearchState(
                seed=state.seed,
                plan=state.plan,
                tool_calls=state.tool_calls,
                simulated_molecules=state.simulated_molecules,
                conclusions=state.conclusions,
                critique=response.content,
            )

        async def update(state: SearchState) -> SearchState:
            results_str = "\n".join(
                f"{molecule}\t\t{energy}"
                for molecule, energy in state.simulated_molecules.items()
            )
            conclusions = "\n\t".join(state.conclusions)
            response = await self.reasoning_llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are expert chemist analyzing the results of "
                            "simulations. Update the given plan based on the "
                            "results so far, the conclusions drawn and the "
                            "critique given. Ground your updates in current "
                            "results, but also knowledge of chemistry and "
                            "physics. You should output a new, stand-alone "
                            "plan that does not make reference to the "
                            "existing plan. If all of the experiments "
                            "suggested by the plan have been carried out, "
                            "suggest more experiments. Note: the only "
                            "experiment your lab is capable of running is "
                            "calculating the QED (drug-likeness) of proposed "
                            "molecules."
                        ),
                    ),
                    HumanMessage(
                        content=(
                            f"Plan: {state.plan}\n\n"
                            "Simulation Results:\n"
                            "Molecule\t\tQED\n"
                            f"{results_str}\n\n"
                            "Conclusions:\n"
                            f"\t{conclusions}\n\n"
                            "Critique:\n"
                            f"\t{state.critique}"
                        ),
                    ),
                ],
            )
            logger.info(f"Update: {response}")

            return SearchState(
                seed=state.seed,
                plan=response.content,
                tool_calls=state.tool_calls,
                simulated_molecules=state.simulated_molecules,
                conclusions=state.conclusions,
                critique=state.critique,
            )

        async def should_continue(
            state: SearchState,
        ) -> Literal["critique", END]:  # type: ignore[valid-type]
            if not shutdown.is_set():
                return "critique"
            return END

        # Build workflow
        agent_builder = StateGraph(SearchState)

        # Add nodes
        agent_builder.add_node("plan", plan)
        agent_builder.add_node("tool_calling", tool_calling)
        agent_builder.add_node("simulate", simulate)
        agent_builder.add_node("conclude", conclude)
        agent_builder.add_node("critique", critique)
        agent_builder.add_node("update", update)

        # Add edges to connect nodes
        agent_builder.add_edge(START, "plan")
        agent_builder.add_edge("plan", "tool_calling")
        agent_builder.add_edge("tool_calling", "simulate")
        agent_builder.add_edge("simulate", "conclude")
        agent_builder.add_conditional_edges(
            "conclude",
            should_continue,
            ["critique", END],
        )
        agent_builder.add_edge("critique", "update")
        agent_builder.add_edge("update", "tool_calling")

        # Compile the agent
        agent = agent_builder.compile()

        # Run until the agent is terminated
        await agent.ainvoke(self.search_state, {"recursion_limit": 10000})

    @action
    async def report(self) -> list[tuple[str, float]]:
        """Summarize findings so far."""
        best_molecules = sorted(
            self.molecule_cache.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return best_molecules
