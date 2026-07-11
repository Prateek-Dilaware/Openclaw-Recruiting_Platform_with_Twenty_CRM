import logging
from typing import Dict, Any, Callable
from app.agents.jd_agent import JDAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.interview_agent import InterviewAgent
from app.agents.retrospective_agent import RetrospectiveAgent

logger = logging.getLogger(__name__)

class OpenClawService:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._skills: Dict[str, Callable] = {}
        
        # Bootstrap and register existing platform agents
        self.register_agent("jd_agent", JDAgent())
        self.register_agent("scheduling_agent", SchedulingAgent())
        self.register_agent("interview_agent", InterviewAgent())
        self.register_agent("retrospective_agent", RetrospectiveAgent())
        logger.info("OpenClawService bridge initialized. Standard agents registered.")

    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """Registers a recruiting agent into the OpenClaw execution system."""
        self._agents[agent_name] = agent_instance
        logger.info(f"OpenClaw registered agent: {agent_name}")

    def register_skill(self, skill_name: str, skill_fn: Callable) -> None:
        """Registers a custom capability tool (e.g. CRM skill) for agent usage."""
        self._skills[skill_name] = skill_fn
        logger.info(f"OpenClaw registered skill tool: {skill_name}")

    def get_agent(self, agent_name: str) -> Any:
        """Retrieves an agent instance by registered key."""
        if agent_name not in self._agents:
            raise KeyError(f"OpenClaw Agent '{agent_name}' is not registered.")
        return self._agents[agent_name]

    async def execute_task(self, agent_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Executes a recruiting task through the agent bridge.
        Enables logging and future multi-agent routing intercepts.
        """
        logger.info(f"OpenClaw executing task: {agent_name} -> {method_name}")
        agent = self.get_agent(agent_name)
        
        if not hasattr(agent, method_name):
            raise AttributeError(f"Agent '{agent_name}' has no method '{method_name}'")
            
        method = getattr(agent, method_name)
        # Execute the agent task
        result = await method(*args, **kwargs)
        return result
