from .base_agent import BaseAgent


class AgentJ(BaseAgent):
    AGENT_ID = "agent_j"
    MODEL = "claude-opus-4-6"
    PROMPT_FILE = "prompts/agent_j.txt"
    MAX_TOKENS = 16000
