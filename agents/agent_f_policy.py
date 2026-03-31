from .base_agent import BaseAgent


class AgentF(BaseAgent):
    AGENT_ID = "agent_f"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_f.txt"
