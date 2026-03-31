from .base_agent import BaseAgent


class AgentG(BaseAgent):
    AGENT_ID = "agent_g"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_g.txt"
