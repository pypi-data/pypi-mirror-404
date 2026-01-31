# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .conversation import Conversation

__all__ = ["ConversationRetrieveResponse", "ConversationRetrieveResponseMessage"]


class ConversationRetrieveResponseMessage(BaseModel):
    id: str
    """Unique message ID"""

    content: Optional[str] = None
    """Message content"""

    conversation_id: str = FieldInfo(alias="conversationId")
    """Conversation ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the message was created"""

    name: Optional[str] = None
    """Tool name (for tool messages)"""

    role: Literal["system", "user", "assistant", "tool"]
    """Message role"""

    tool_call_id: Optional[str] = FieldInfo(alias="toolCallId", default=None)
    """Tool call ID (for tool messages)"""

    tool_calls: Optional[object] = FieldInfo(alias="toolCalls", default=None)
    """Tool calls (for assistant messages)"""


class ConversationRetrieveResponse(Conversation):
    messages: List[ConversationRetrieveResponseMessage]
    """Conversation messages"""
