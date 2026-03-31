from .base_agent import BaseAgent


class AgentA(BaseAgent):
    AGENT_ID = "agent_a"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_a.txt"
