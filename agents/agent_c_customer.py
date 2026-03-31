from .base_agent import BaseAgent


class AgentC(BaseAgent):
    AGENT_ID = "agent_c"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_c.txt"
