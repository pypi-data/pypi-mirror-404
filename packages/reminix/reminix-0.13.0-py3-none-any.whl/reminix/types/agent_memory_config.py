# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["AgentMemoryConfig"]


class AgentMemoryConfig(BaseModel):
    """Memory feature configuration"""

    enabled: bool
    """Whether memory is enabled for this agent"""
