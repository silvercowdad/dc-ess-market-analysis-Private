from .base_agent import BaseAgent


class AgentI(BaseAgent):
    AGENT_ID = "agent_i"
    MODEL = "claude-opus-4-6"
    PROMPT_FILE = "prompts/agent_i.txt"
    MAX_TOKENS = 16000
