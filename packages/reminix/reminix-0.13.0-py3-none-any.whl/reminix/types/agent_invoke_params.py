# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

__all__ = ["AgentInvokeParamsBase", "Context", "AgentInvokeParamsNonStreaming", "AgentInvokeParamsStreaming"]


class AgentInvokeParamsBase(TypedDict, total=False):
    context: Context
    """Optional context for the agent execution"""


class ContextTyped(TypedDict, total=False):
    """Optional context for the agent execution"""

    identity: Dict[str, Optional[object]]
    """Identity fields for conversation scoping (e.g., user_id, tenant_id)"""


Context: TypeAlias = Union[ContextTyped, Dict[str, Optional[object]]]


class AgentInvokeParamsNonStreaming(AgentInvokeParamsBase, total=False):
    stream: Literal[False]
    """Enable streaming response (SSE)"""


class AgentInvokeParamsStreaming(AgentInvokeParamsBase):
    stream: Required[Literal[True]]
    """Enable streaming response (SSE)"""


AgentInvokeParams = Union[AgentInvokeParamsNonStreaming, AgentInvokeParamsStreaming]
