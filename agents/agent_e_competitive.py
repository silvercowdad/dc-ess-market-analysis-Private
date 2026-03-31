from .base_agent import BaseAgent


class AgentE(BaseAgent):
    AGENT_ID = "agent_e"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_e.txt"
