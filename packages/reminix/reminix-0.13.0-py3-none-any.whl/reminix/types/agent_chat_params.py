# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .chat_message_param import ChatMessageParam

__all__ = ["AgentChatParamsBase", "Context", "AgentChatParamsNonStreaming", "AgentChatParamsStreaming"]


class AgentChatParamsBase(TypedDict, total=False):
    messages: Required[Iterable[ChatMessageParam]]
    """Array of chat messages"""

    context: Context
    """Optional context for the agent execution"""

    conversation_id: str
    """Conversation ID to continue an existing conversation"""


class ContextTyped(TypedDict, total=False):
    """Optional context for the agent execution"""

    identity: Dict[str, Optional[object]]
    """Identity fields for conversation scoping (e.g., user_id, tenant_id)"""


Context: TypeAlias = Union[ContextTyped, Dict[str, Optional[object]]]


class AgentChatParamsNonStreaming(AgentChatParamsBase, total=False):
    stream: Literal[False]
    """Enable streaming response"""


class AgentChatParamsStreaming(AgentChatParamsBase):
    stream: Required[Literal[True]]
    """Enable streaming response"""


AgentChatParams = Union[AgentChatParamsNonStreaming, AgentChatParamsStreaming]
