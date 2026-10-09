"""Example: launch a UserAgent and a MonitoredAgent and exchange messages.

Both agents run inside a local ProcessPoolExecutor so no remote
infrastructure is required to run this example.
"""

from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from uuid import UUID

import dotenv
from academy.exchange.cloud import HttpExchangeFactory
from academy.identifier import AgentId
from academy.manager import Manager
from academy_dashboard.agents import Sleeper, Spinner
from globus_compute_sdk import Executor as GlobusExecutor


async def main(user_agent_id: UUID) -> None:
    """Launch MonitoredAgents across facilities with Globus Compute."""
    executors = {
        "nersc": GlobusExecutor(endpoint_id="07b73b75-d534-428f-acd8-003b01a166f5"),
        #'anvil': GlobusExecutor(
        #     endpoint_id='5aafb4c1-27b2-40d8-a038-a0277611868f',
        #     user_endpoint_config={'worker_init': 'source ~/setup_env.sh'}),
        #'frontera': GlobusExecutor(endpoint_id='933cff43-f895-4b92-a5c0-536a5162b8ec'),
        #'polaris': GlobusExecutor(
        #    endpoint_id='9a947ba5-f537-4681-acf3-cc66485aadec',
        #    user_endpoint_config={
        #        'queue': 'debug',
        #        'walltime': '00:10:00',
        #        'config_key': 'source /home/yadunand/setup_academy.sh',
        #        'account': 'ModCon',
        #    },
        # ),
        "local": ProcessPoolExecutor(max_workers=4),
    }

    async with await Manager.from_exchange_factory(
        factory=HttpExchangeFactory(),
        executors=executors,
    ) as manager:
        # 1. Launch UserAgent first so its handle can be passed to the worker.
        agent_id = AgentId(uid=user_agent_id, name="UserAgent")
        user_agent_handle = manager.get_handle(agent_id)

        # 2. Launch a few agents, and pass them the user_agent_handle
        handles = []
        for site in executors:
            spinner = await manager.launch(
                Spinner,
                kwargs={"user_agent_handle": user_agent_handle},
                executor=site,
            )
            handles.append(spinner)

        # Force a user query prompt from a remote agent
        await spinner.trigger_user_query()

        sleeper = await manager.launch(
            Sleeper,
            kwargs={"user_agent_handle": user_agent_handle},
            executor="local",
        )

        handles.append(sleeper)

        # 3. Trigger work on the worker — log messages are forwarded automatically.
        await spinner.run(iterations=5)

        # 4. Shutdown agents and exit
        logging.info("All done!")
        [await handle.shutdown() for handle in handles]


if __name__ == "__main__":
    # Load settings from settings.env in the project root
    dotenv.load_dotenv(dotenv.find_dotenv("settings.env"))
    user_agent_id = os.environ["USER_AGENT_ID"]
    raise SystemExit(asyncio.run(main(user_agent_id=UUID(user_agent_id))))
