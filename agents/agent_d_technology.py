from .base_agent import BaseAgent


class AgentD(BaseAgent):
    AGENT_ID = "agent_d"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_d.txt"
