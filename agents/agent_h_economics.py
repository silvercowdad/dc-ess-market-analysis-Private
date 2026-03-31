from .base_agent import BaseAgent


class AgentH(BaseAgent):
    AGENT_ID = "agent_h"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/agent_h.txt"
