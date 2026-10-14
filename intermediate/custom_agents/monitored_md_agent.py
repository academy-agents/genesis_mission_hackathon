"""MolDesignAgent that sends its logs and stats to the Academy Dashboard."""

from __future__ import annotations

from academy.handle import Handle
from academy_dashboard import MonitoredAgent, UserAgent

from intermediate.custom_agents.mol_design_agents import MolDesignAgent


class MonitoredMolDesignAgent(MolDesignAgent, MonitoredAgent):
    """MolDesignAgent with the MonitoredAgent dashboard features.

    MRO: MonitoredMolDesignAgent -> MolDesignAgent -> MonitoredAgent -> Agent.
    MolDesignAgent does not call super() in its hooks, so these methods call
    both parents explicitly.
    """

    def __init__(
        self,
        start_molecule: str,
        llm_model: str,
        base_url: str,
        api_key: str,
        user_agent_handle: Handle[UserAgent],
    ) -> None:
        MonitoredAgent.__init__(self, user_agent_handle=user_agent_handle)
        MolDesignAgent.__init__(self, start_molecule, llm_model, base_url, api_key)

    async def agent_on_startup(self) -> None:
        # Start the log forwarding first, so the dashboard gets the startup logs
        await MonitoredAgent.agent_on_startup(self)
        await MolDesignAgent.agent_on_startup(self)

    async def agent_on_shutdown(self) -> None:
        await MolDesignAgent.agent_on_shutdown(self)
        await MonitoredAgent.agent_on_shutdown(self)
