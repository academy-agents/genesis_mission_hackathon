"""Run the MolDesignAgent discovery campaign on your own computer.

NOTE:: If you are using MAG, this example will work only within DOE lab networks

Same as remote_discovery_campaign.py, but the agents run in this process and talk
over a local exchange, so no Globus Compute endpoint or Academy cloud
exchange is needed. Only the MAG settings in settings.env are required.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import dotenv
from academy.exchange import LocalExchangeFactory
from academy.manager import Manager

from intermediate.custom_agents.mol_design_agents import MolDesignAgent

logger = logging.getLogger(__name__)


async def main(rounds: int, interval: float) -> int:
    dotenv.load_dotenv(dotenv.find_dotenv("settings.env", usecwd=True))

    # We launch the MolDesignAgents on Threads
    async with await Manager.from_exchange_factory(
        factory=LocalExchangeFactory(),
        executors=ThreadPoolExecutor(max_workers=4),
    ) as manager:
        seeds = [
            "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
            "CC1=C(O)N=C(O)N1",  # 5-Methylhydantoin (enol form)
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

        print("Starting local discovery campaign")
        print("=" * 80)
        for _ in range(rounds):
            await asyncio.sleep(interval)
            for i, agent in enumerate(agents):
                print(f"Progress report from agent {i}")
                report = await agent.report()
                print(f"Number of molecules simulated: {len(report)}")
                print(f"Five best molecules: {report[:5]}")
            print("=" * 80)

        for agent in agents:
            await agent.shutdown()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rounds",
        type=int,
        default=4,
        help="Number of progress reports before shutting down",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=30,
        help="Seconds between progress reports",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(asyncio.run(main(args.rounds, args.interval)))
