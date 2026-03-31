from .base_agent import BaseAgent


class AgentB(BaseAgent):
    AGENT_ID = "agent_b"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_b.txt"
