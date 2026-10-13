from __future__ import annotations

import asyncio
import logging
import os

import dotenv
from academy.exchange import HttpExchangeFactory
from academy.manager import Manager
from globus_compute_sdk import Executor as GlobusExecutor

from intermediate.custom_agents.mol_design_agents import MolDesignAgent

logger = logging.getLogger(__name__)


async def main() -> int:

    # 1. Update this to match your preferred HPC system
    dotenv.load_dotenv(dotenv.find_dotenv("settings.env", usecwd=True))
    executor = GlobusExecutor(
        endpoint_id=os.environ["AURORA_ENDPOINT_ID"],
        # Run the workers in the repo venv from `uv sync`, which has the agent code
        user_endpoint_config={
            "worker_init": "source $HOME/genesis_mission_hackathon/.venv/bin/activate"
        },
    )

    async with await Manager.from_exchange_factory(
        factory=HttpExchangeFactory(),
        executors=executor,
    ) as manager:
        seeds = [
            "CNC(N)=O",
            "CC1=C(O)N=C(O)N1",
        ]

        # We spawn agents that will process each molecule independently
        agents = []
        for molecule in seeds:
            agents.append(
                await manager.launch(
                    MolDesignAgent,
                    args=(molecule,),
                    kwargs={
                        "llm_model": os.environ["LLM_MODEL"],
                        "base_url": os.environ["OPENAI_BASE_URL"],
                        "api_key": os.environ["AMSC_TOKEN"],
                    },
                ),
            )

        print("Starting discovery campaign")
        print("=" * 80)
        while True:
            await asyncio.sleep(30)
            for i, agent in enumerate(agents):
                print(f"Progress report from agent {i}")
                report = await agent.report()
                print(f"Number of molecules simulated: {len(report)}")
                print(f"Five best molecules: {report[:5]}")
            print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
