# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .agent_memory_config import AgentMemoryConfig
from .agent_knowledge_base_config import AgentKnowledgeBaseConfig

__all__ = ["AgentConfig"]


class AgentConfig(BaseModel):
    """Agent configuration (for managed agents)"""

    model: str
    """Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")"""

    provider: Literal["openai", "anthropic"]
    """LLM provider"""

    system_prompt: str = FieldInfo(alias="systemPrompt")
    """System prompt for the agent"""

    tools: List[str]
    """List of tools available to the agent"""

    knowledge_base: Optional[AgentKnowledgeBaseConfig] = FieldInfo(alias="knowledgeBase", default=None)
    """Knowledge base feature configuration"""

    max_iterations: Optional[float] = FieldInfo(alias="maxIterations", default=None)
    """Maximum tool call iterations"""

    memory: Optional[AgentMemoryConfig] = None
    """Memory feature configuration"""

    require_approval: Optional[bool] = FieldInfo(alias="requireApproval", default=None)
    """Whether to require approval for tool calls"""
